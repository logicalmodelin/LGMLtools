bl_info = {
    "name": "BBOX Box Creator",
    "blender": (3, 0, 0),
    "category": "Object",
    "author": "modelin",
    "description": "Create a new box aligned to the BBOX of selected objects."
}

import bpy
from mathutils import Vector, Matrix

class OBJECT_OT_CreateBBoxBox(bpy.types.Operator):
    bl_idname = "object.create_bbox_box"
    bl_label = "Create BBOX Box"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if context.area.type != 'VIEW_3D':
            return {"CANCELLED"}

        selected_objects = context.selected_objects

        if not selected_objects:
            return {"CANCELLED"}

        # Calculate the combined BBOX
        min_corner = Vector((float('inf'), float('inf'), float('inf')))
        max_corner = Vector((float('-inf'), float('-inf'), float('-inf')))

        for obj in selected_objects:
            matrix_world = obj.matrix_world
            bbox_corners = [matrix_world @ Vector(corner) for corner in obj.bound_box]
            for corner in bbox_corners:
                min_corner = Vector((min(min_corner[i], corner[i]) for i in range(3)))
                max_corner = Vector((max(max_corner[i], corner[i]) for i in range(3)))

        bbox_center = (min_corner + max_corner) / 2
        bbox_dimensions = max_corner - min_corner

        # Create a new box
        bpy.ops.mesh.primitive_cube_add()
        new_box = context.active_object
        new_box.name = "BBOX_Box"

        # Set the scale and location of the new box based on the BBOX
        new_box.scale = bbox_dimensions / 2
        new_box.location = bbox_center

        return {"FINISHED"}

# class BBOXBoxCreatorPanel(bpy.types.Panel):
#     bl_idname = "OBJECT_PT_bbox_box_creator"
#     bl_label = "BBOX Box Creator"
#     bl_space_type = "VIEW_3D"
#     bl_region_type = "UI"
#     bl_category = "Tools"

#     def draw(self, context):
#         layout = self.layout
#         layout.operator_context = 'INVOKE_DEFAULT'
#         layout.operator(OBJECT_OT_CreateBBoxBox.bl_idname)

class VIEW3D_MT_BBOXBoxMenu(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_bbox_box_menu"
    bl_label = "BBOX Box Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator(OBJECT_OT_CreateBBoxBox.bl_idname, icon='MESH_CUBE')

# Registration
classes = [
    OBJECT_OT_CreateBBoxBox,
    # BBOXBoxCreatorPanel,
    VIEW3D_MT_BBOXBoxMenu
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_CreateBBoxBox.bl_idname, text="Create BBOX Box", icon='MESH_CUBE')

if __name__ == "__main__":
    register()
