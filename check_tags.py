import re

def check_tags(filename):
    with open(filename, 'r') as f:
        content = f.read()

    stack = []
    # Tags that are void or often self-closing in HTML5
    void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    # SVG tags also often don't need closing in some contexts or are self-closed
    # But for simplicity let's treat them as self-closing or regular.
    # Actually, SVG is XML-like.
    
    # Let's just track all tags and see where it breaks.
    
    for match in re.finditer(r'<(/?)([a-zA-Z1-6]+)(?:\s+[^>]*)?>', content):
        tag_name = match.group(2).lower()
        is_closing = match.group(1) == '/'
        line_no = content.count('\n', 0, match.start()) + 1
        
        if tag_name in void_tags:
            continue
            
        # Handle self-closing tags like <path ... />
        if not is_closing and match.group(0).endswith('/>'):
            continue

        if is_closing:
            if not stack:
                print(f"Error: Unexpected closing tag </{tag_name}> at line {line_no}")
            else:
                last_tag, last_line = stack.pop()
                if last_tag != tag_name:
                    print(f"Error: Mismatched tag </{tag_name}> at line {line_no} (expected closing for <{last_tag}> from line {last_line})")
                    # Push back the mismatched tag to try to recover?
                    # No, just keep going.
        else:
            stack.append((tag_name, line_no))
    
    for tag_name, line_no in stack:
        if tag_name not in ['html', 'head', 'body']:
            print(f"Error: Unclosed tag <{tag_name}> from line {line_no}")

check_tags('/home/looser/nutriTracker/templates/index.html')
