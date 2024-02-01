import bpy
import os

from bpy.types import Operator
from bpy.props import CollectionProperty, StringProperty


def register():
    pass

def unregister():
    pass


if bpy.app.version >= (4, 1, 0):
    class TEXTIFY_FH_import_scripts(bpy.types.FileHandler):
        bl_idname = "TEXTIFY_FH_import_scripts"
        bl_label = "Import Script"
        bl_import_operator = "textify.import_script"
        bl_file_extensions = ".py;.txt;.json"

        @classmethod
        def poll_drop(cls, context):
            return True


    class TEXTIFY_FH_install_addons(bpy.types.FileHandler):
        bl_idname = "TEXTIFY_FH_install_addons"
        bl_label = "Install Addon"
        bl_import_operator = "wm.install_addon"
        bl_file_extensions = ".zip;.py"

        @classmethod
        def poll_drop(cls, context):
            return True


    class TEXTIFY_OT_import_script(Operator):
        bl_idname = "textify.import_script"
        bl_label = "Import Script"
        bl_description = "Import Script"
        bl_options = {'INTERNAL'}

        files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'SKIP_SAVE'})
        directory: StringProperty(subtype='DIR_PATH')

        def execute(self, context):
            for file in self.files:
                filepath = os.path.join(self.directory, file.name)
                text = bpy.data.texts.load(filepath)
                if text:
                    imported_scripts.append(file.name)
                else:
                    self.report({'ERROR'}, f"Failed to import script {file.name}")

            if imported_scripts:
                self.report({'INFO'}, f"Imported scripts {', '.join(imported_scripts)} successfully")

            return {'FINISHED'}


    class TEXTIFY_OT_install_addon(bpy.types.Operator):
        bl_idname = "wm.install_addon"
        bl_label = "Install Addon"
        bl_description = "Install Addon"
        bl_options = {'INTERNAL'}

        files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'SKIP_SAVE'})
        directory: bpy.props.StringProperty(subtype='DIR_PATH')
        
        @classmethod
        def poll(cls, context):
            # Check if the file is a Python file
            for file in context.operator.filelist:
                filepath = os.path.join(context.operator.directory, file.name)
                if filepath.lower().endswith('.py'):
                    # If it is a Python file, check if it contains 'bl_info'
                    with open(filepath, 'r') as f:
                        if 'bl_info' in f.read():
                            return True
            else:
                # If it is not a Python file, the operator can be invoked
                return True

            # If none of the above conditions are met, the operator cannot be invoked
            return False

        def execute(self, context):
            bpy.data.window_managers["WinMan"].addon_search = ""
            
            version = '.'.join([str(v) for v in bpy.app.version[:2]])  # Only use the major and minor version numbers
            addon_path = os.path.join(os.getenv('APPDATA'), r'Blender Foundation\Blender', version, r'scripts\addons')

            successful_addons = []
            for file in self.files:
                filepath = os.path.join(self.directory, file.name)
                bpy.ops.preferences.addon_install(filepath=filepath, overwrite=True)

                # Get the last created file or folder in the specified directory
                addon_name = self.get_last_created_item(addon_path)

                if addon_name:
                    bpy.ops.preferences.addon_enable(module=addon_name)

                    if addon_name in bpy.context.preferences.addons.keys():
                        successful_addons.append(addon_name)
                    else:
                        self.report({'WARNING'}, f"Failed to enable addon {addon_name}")
                else:
                    self.report({'ERROR'}, "Failed to install addon")

            if successful_addons:
                self.report({'INFO'}, f"Installed addon {', '.join(successful_addons)} successfully")

            if len(successful_addons) == 1:
                bpy.ops.screen.userpref_show()
            return {'FINISHED'}

        def get_last_created_item(self, folder_path):
            folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]

            if folders:
                last_folder = max(folders, key=lambda item: os.path.getctime(os.path.join(folder_path, item)))
                return last_folder  # Return the folder name
            else:
                return None


    classes = (
        TEXTIFY_FH_import_scripts,
        TEXTIFY_FH_install_addons,
        TEXTIFY_OT_import_script,
        TEXTIFY_OT_install_addon,
    )


    def register():
        for cls in classes:
            bpy.utils.register_class(cls)


    def unregister():
        for cls in classes:
            bpy.utils.unregister_class(cls)
