# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; version 3
#  of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Character Count",
    "blender": (2, 80, 0),
    "category": "Text Editor",
}

import bpy

def character_count(self, context):
    layout = self.layout

    layout.separator_spacer()

    # Get the current text data
    text = bpy.context.space_data.text
    if text:
        total_characters = sum(len(line.body) for line in text.lines)

        # Check if there is any text selected
        if text.select_set and (text.current_line_index != text.select_end_line_index or text.current_character != text.select_end_character):
            start_line, end_line = sorted([text.current_line_index, text.select_end_line_index])
            start_char, end_char = sorted([text.current_character, text.select_end_character])

            # Calculate selected characters based on selection direction
            if start_line == end_line:
                selected_characters = abs(end_char - start_char)
            else:
                selected_characters = len(text.lines[start_line].body[start_char:])
                selected_characters += sum(len(line.body) for line in text.lines[start_line+1:end_line])
                selected_characters += len(text.lines[end_line].body[:end_char])

            cursor_line = text.select_end_line_index + 1
            cursor_column = text.select_end_character + 1
            layout.label(text=f"Ln {cursor_line}, Col {cursor_column}   |   {selected_characters} of {total_characters} characters")
        else:
            # Display the current character count
            cursor_line = text.current_line_index + 1
            cursor_column = text.current_character + 1
            layout.label(text=f"Ln {cursor_line}, Col {cursor_column}   |   {total_characters} characters")

def register():
    bpy.types.TEXT_HT_footer.append(character_count)

def unregister():
    bpy.types.TEXT_HT_footer.remove(character_count)

if __name__ == "__main__":
    register()
