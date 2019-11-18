#!/usr/bin/env python

import sys
import pipes
import os

for html_file_path in sys.argv[1:]:
    with open(html_file_path, 'r') as my_file:
        text_html = my_file.read()
        first_dashes_end = text_html.find("---") + 3
        second_dashes_end = text_html.find("---", first_dashes_end) + 3
        begin_text = text_html[:second_dashes_end]
        remaining_text = text_html[second_dashes_end:]
        command = "kramdown --html-to-native --line-width 220  -i html -o remove_html_tags,kramdown --remove-span-html-tags"
        kramdown = pipes.Template()
        kramdown.append(command,"--")
        f = kramdown.open('pipefile', 'w')
        f.write(remaining_text)
        f.close()
    with open('pipefile', "r") as kramdown_results:
        new_remaining_text = kramdown_results.read()
        new_remaining_text = new_remaining_text.replace("</p>", "\n\n").replace("&ndash;", "--")
        print(new_remaining_text)
        new_name, _extension = os.path.splitext(html_file_path)
        new_name +=  ".md"
    with open(new_name, "w") as kramdown_file:
        kramdown_file.write(begin_text + "\n\n" + new_remaining_text)
            
