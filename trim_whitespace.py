# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
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


import bpy


def draw_menu(self, context):
    """Draw the menu."""
    prefs = bpy.context.preferences.addons[__package__].preferences

    if prefs.enable_trim_whitespace:
        text_block = context.space_data.text
        if text_block is not None and any(line.body.rstrip() != line.body for line in text_block.lines):
            layout = self.layout
            layout.operator("text.trim_whitespaces", icon="GRIP")

class TEXT_OT_trim_whitespaces(bpy.types.Operator):
    """Define the operator for the remove whitespaces function."""
    bl_idname = "text.trim_whitespaces"
    bl_label = "Trim Whitespaces"

    @classmethod
    def poll(cls, context):
        text = context.space_data.text
        return text is not None

    def execute(self, context):
        text_block = context.space_data.text
        lines = text_block.lines
        removed_chars_count = 0

        for i, line in enumerate(lines):
            original_length = len(line.body)
            lines[i].body = line.body.rstrip()
            removed_chars_count += original_length - len(lines[i].body)

        if removed_chars_count > 0:
            self.report({'INFO'}, f"Removed {removed_chars_count} trailing whitespace characters.")
        else:
            self.report({'INFO'}, "No trailing whitespace characters to remove.")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(TEXT_OT_trim_whitespaces)
    bpy.types.TEXT_MT_context_menu.prepend(draw_menu)


def unregister():
    bpy.utils.unregister_class(TEXT_OT_trim_whitespaces)
    bpy.types.TEXT_MT_context_menu.remove(draw_menu)
