
import unicodedata
import re

def normalize_unicode_to_ascii(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

def parse_requirements(req_str):
    # Tokenize the requirement string
    def tokenize(req_str):
        # Tokenize phrases and special tokens
        pattern = r'(\(|\)|;|\bor\b)'
        parts = re.split(pattern, req_str)

        tokens = []
        course_pattern = re.compile(r'[A-Za-z]{1,4}\s?\d{4}')

        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Check if the token is one of the special delimiters
            if part in ['(', ')', ';', 'or']:
                tokens.append(part)
            else:
                # Get actual course
                matches = course_pattern.findall(part)
                if matches:
                    tokens.extend(matches)
                    
        return tokens

    # parse_sequence handles a sequence of tokens possibly containing:
    # - parentheses (for grouping)
    # - semicolons (for separating subrequirements)
    # - or (for branching)
    def parse_sequence(tokens, start=0, depth=0):
        requirements = []
        current_tokens = []
        i = start
        while i < len(tokens):
            token = tokens[i]
            
            if token == '(':
                group, new_i = parse_sequence(tokens, i+1, depth+1)
                requirements.append(group)
                i = new_i
            elif token == ')':
                if current_tokens:
                    # Process whatever is in current tokens before closing parenthesis
                    requirements.append(parse_subrequirements(" ".join(current_tokens)))
                    current_tokens = []
                return condense_requirements(requirements), i+1
            elif token == ';':
                # Semicolon indicates break between subrequirements
                if current_tokens:
                    requirements.append(parse_subrequirements(" ".join(current_tokens)))
                    current_tokens = []
                i += 1
            elif token == 'or':
                # OR at the current level means we combine what we have and continue
                # If current_tokens is not empty, that forms one requirement part
                if current_tokens:
                    requirements.append(parse_subrequirements(" ".join(current_tokens)))
                    current_tokens = []
                # We'll mark an OR branch by continuing to parse forward.
                # Let's store an 'or' marker that the caller can condense.
                requirements.append('OR')
                i += 1
            else:
                # Just part of a course requirement phrase
                current_tokens.append(token)
                i += 1
        
        if current_tokens:
            requirements.append(parse_subrequirements(" ".join(current_tokens)))
        
        return condense_requirements(requirements), i

    tokens = tokenize(req_str)
    parsed, _ = parse_sequence(tokens, 0, 0)
    return parsed

def parse_subrequirements(req_str):
    parts = re.split(r'\bor\b', req_str)
    parts = [p.strip() for p in parts if p.strip()]
    # If there's more than one part, this is a set of alternatives
    if len(parts) > 1:
        # Extract course names before "with a minimum grade"
        # Adjust this parsing if you need to store the grade as well
        courses = [extract_course_name(p) for p in parts]
        return courses
    else:
        # Just a single requirement
        return extract_course_name(parts[0])

def extract_course_name(req_phrase):
    # regex for courses 1-4 letters, 4 nums
    match = re.match(r'([A-Za-z]{1,4}\s\d{4})', req_phrase)
    if match:
        return match.group(1)
    return req_phrase  # fallback if not matched

def condense_requirements(req_list):
    # Check if there's an 'OR' in req_list
    if 'OR' not in req_list:
        # No OR, if single element just return it
        # If multiple elements separated by semicolons, we might want to nest them as Requirements
        if len(req_list) == 1:
            return req_list[0]
        else:
            # Multiple subrequirements; label them as Requirement1, Requirement2, etc.
            return {f"Requirement{i+1}": req for i, req in enumerate(req_list)}
    else:
        # There is an OR
        # Split by OR and condense each side
        or_segments = []
        current_segment = []
        for item in req_list:
            if item == 'OR':
                # End of a segment
                or_segments.append(current_segment)
                current_segment = []
            else:
                current_segment.append(item)
        if current_segment:
            or_segments.append(current_segment)

        # Now we have something like [[...segment1...], [...segment2...]]
        # Condense each segment and then make a list of them
        condensed_segments = []
        for seg in or_segments:
            c = condense_requirements(seg)
            condensed_segments.append(c)
        
        # If top-level OR, just return a list of the options:
        return condensed_segments
    