import bpy

bl_info = {
    "name": "Trim Whitespace",
    "author": "Jishnu jithu",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "description": "Removes all trailing whitespace characters in the current text block.",
    "location": "Text Editor > Context Menu > Trim Whitespace",
    "category": "Text Editor"
}

def draw_menu(self, context):
    """Draw the menu."""
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

if __name__ == "__main__":
    register()
