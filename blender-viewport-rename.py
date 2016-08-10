import bpy
import re

bl_info = {
    "name": "Viewport Rename",
    "author": "poor",
    "version": (0, 1),
    "blender": (2, 77, 0),
    "location": "3D View > Ctrl + R",
    "category": "3D View"
}

class ViewportRenameSettings(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="New name")

class ViewportRenameOperator(bpy.types.Operator):
    """Rename Objects in 3d View"""
    bl_idname = "view3d.viewport_rename"
    bl_label = "Viewport Renamer"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (bool(context.selected_objects))

    def invoke(self, context, event):
        scn = context.scene
        scn.viewport_rename.name = context.active_object.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        col = layout.column()
        col.prop(scn.viewport_rename, "name", expand=True)

    def execute(self, context):
        scn = context.scene
        user_input = scn.viewport_rename.name

        reverse = False
        if user_input.endswith("#r"):
            reverse = True
            user_input = user_input[:-1]

        suff = re.findall("#+$", user_input)
        if user_input and suff:
            number = ('%0'+str(len(suff[0]))+'d', len(suff[0]))
            real_name = re.sub("#", '', user_input)           

            objs = context.selected_objects[::-1] if reverse else context.selected_objects
            names_before = [n.name for n in objs]
            for c, o in enumerate(objs, start=1):
                o.name = (real_name + (number[0] % c))
            self.report({'INFO'}, "Renamed {}".format(", ".join(names_before)))
            return {'FINISHED'}

        elif user_input:
            old_name = context.active_object.name
            context.active_object.name = user_input
            self.report({'INFO'}, "{} renamed to {}".format(old_name, user_input))
            return {'FINISHED'}

        else:
            self.report({'INFO'}, "No input, operation cancelled")
            return {'CANCELLED'}

# ------------------------------------------------------------------------
#    register and unregister functions
# ------------------------------------------------------------------------

addon_keymaps = []

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.viewport_rename = bpy.props.PointerProperty(type=ViewportRenameSettings)

    # handle the keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(ViewportRenameOperator.bl_idname, type='R', value='PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))

def unregister():

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.viewport_rename

if __name__ == "__main__":
    register()