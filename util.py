
import unicodedata
import re



def normalize_unicode_to_ascii(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')



def parse_requirements(req_str):
    # Tokenize the requirement string
    def tokenize(req_str):
        # We'll separate parentheses, semicolons, and the word "or" as special tokens.
        # Everything else is considered part of a requirement phrase.
        # A regex approach: split tokens around ( ), ;, and "or" but keep them
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
                # Attempt to extract valid course tokens
                matches = course_pattern.findall(part)
                # If we found valid course codes, add them
                # If not, we skip the token since it doesn't match the pattern
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
                # Parse a sub-sequence inside parentheses
                group, new_i = parse_sequence(tokens, i+1, depth+1)
                requirements.append(group)
                i = new_i
            elif token == ')':
                # End of a group
                if current_tokens:
                    # Process whatever is in current tokens before closing parenthesis
                    requirements.append(parse_subrequirements(" ".join(current_tokens)))
                    current_tokens = []
                # Return from recursion
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
        
        # End of tokens or parent scope
        if current_tokens:
            requirements.append(parse_subrequirements(" ".join(current_tokens)))
        
        return condense_requirements(requirements), i

    tokens = tokenize(req_str)
    parsed, _ = parse_sequence(tokens, 0, 0)
    return parsed

def parse_subrequirements(req_str):
    """
    Parse a requirement string that might contain 'or' conditions inside it.
    For example: "CS 2510 with a minimum grade of D- or DS 2500 with a minimum grade of D-"
    should return ["CS 2510", "DS 2500"] as a list of alternatives.
    """
    # Split by "or" carefully: We'll just do a simple split since we handled top-level in parsing.
    # Here we assume no nested parentheses. If there are, they'd be handled at a higher level.
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
    """
    Extract the course name from a phrase like "CS 2510 with a minimum grade of D-".
    This might be just taking the first two tokens if the format is consistent,
    or a regex to identify the course code.
    """
    # Let's assume the course format is always <Dept> <Number>, like "CS 2510".
    # We can use a regex: two letters + space + four digits
    match = re.match(r'([A-Za-z]{2}\s\d{4})', req_phrase)
    if match:
        return match.group(1)
    return req_phrase  # fallback if not matched

def condense_requirements(req_list):
    """
    We might have a list with 'OR' tokens splitting them.
    For example: [ {Requirement1: [...]}, 'OR', "EECE 2160" ]
    We can combine these into a structured dictionary.
    We'll produce a structure like:
    {
        "Requirement1": [..., "EECE 2160"]  # if separated by OR at top level
    }
    If multiple ORs appear, we store them as lists.
    """
    # We want something like this approach:
    # - If there's an 'OR' at the top level, the result should be a list of all alternatives.
    # If there's no OR, just return a single requirement or dictionary.
    
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
    