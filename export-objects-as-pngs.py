#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

# GIMP script for exporting several selections to PNGs
# (c) Brandon Phillips 2020
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This very file is the complete source code to the program.
#
#   If you make and redistribute changes to this code, please mark it
#   in reasonable ways as different from the original version. 
#   
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   The GPL v3 licence is available at: https://www.gnu.org/licenses/gpl-3.0.en.html


import os, sys, math, platform, subprocess
from collections import namedtuple
from gimpfu import *
import traceback

def getSelection(image, drawable, folder_name, threshold_int, x_coord, y_coord):
    pdb.gimp_context_set_sample_threshold_int(threshold_int)                                # set fuzzy select threshold to variable
    pdb.gimp_image_select_contiguous_color(image, 0, drawable, x_coord, y_coord)            # grab fuzzy select point at X,Y (defaults to 10,10)
    deleteAndInvertSelection(image, drawable, folder_name)                                  # call delete/invert selection function

def deleteAndInvertSelection(image, drawable, folder_name):
    layerlist = image.layers                                                                # get all layers
    for l in layerlist:                                                                     # for each layer...
        if not l.has_alpha:                                                                 # if the layer doesn't have an alpha channel
            pdb.gimp_layer_add_alpha(l)                                                     # add the alpha channel

    pdb.gimp_edit_clear(image.layers[0])                                                    # delete selection
    pdb.gimp_selection_invert(image)                                                        # invert the selection
    selectionToPath(image, drawable, folder_name)                                           # call selection to path function

def selectionToPath(image, drawable, folder_name):
    pdb.plug_in_sel2path(image, drawable)                                                   # turn selection to path
    path = pdb.gimp_image_get_vectors_by_name(image, "Selection")                           # get path we just made
    splitToPathsAndSave(image, path, folder_name)                                           # call splitToPathsAndSave and pass along the 'image' and the new 'path'

def splitToPathsAndSave(image, path, folder_name):
    file_path = pdb.gimp_image_get_filename (image)                                         # get the currently opened file's relative filepath
    head_tail = os.path.split(file_path)                                                    # split it by filename and directory
    directory = head_tail[0] + "/"                                                          # set dir variable
    file_name = head_tail[1]                                                                # set filename variable 
    file_name = file_name.replace(".png", "")                                               # take out the .png from name
    directory = directory + str(folder_name) + "/"                                          # set directory to current dir + output name

    if not os.path.exists(directory):                                                       # make /output/ dir if not exist
        os.makedirs(directory)
    
    if path == None:
        raise Exception('No active path in image!')
    if not path :
        raise Exception('No elements in active path!')
        
    val = 0
    ignored = 0
    for stroke in path.strokes:                                                             # for each stroke in all of the strokes 
        strokePath = gimp.Vectors(image,'%s [%d]' % (path.name,stroke.ID))                  # get the stroke's path
        points,closed = stroke.points                                                       # set the points for the bezier stroke later
        total_points = len(stroke.points[0])                                                # count the total points in the points array
        if (total_points > 20):                                                             # if > 20 points, not bogus path
            val += 1                                                                        # increment file counter
            gimp.VectorsBezierStroke(strokePath,points,closed)                              # create a new bezier stroke (path) with stroke points
            pdb.gimp_image_insert_vectors(image, strokePath, None,-1)                       # insert vectors as new path in image
            pdb.gimp_image_select_item(image,CHANNEL_OP_REPLACE,strokePath)                 # select the newly created path (path -> selection)
            pdb.gimp_edit_copy(image.layers[0])                                             # copy selection
            new_img = pdb.gimp_edit_paste_as_new()                                          # paste clipboard as new image
            drawable = pdb.gimp_image_active_drawable(new_img)                              # get the active drawable from the new image
            img_name = file_name + str(val) + ".png"                                        # set the new filename
            pdb.file_png_save_defaults(new_img, drawable, directory + img_name, img_name)   # save it with PNG defaults as [original dir]/output/[original file][iteration].png
            strokePath.visible = True                                                       # mark path as visible
        else: 
            ignored += 1                                                                    # count bogus paths
    path.visible=False
    gimp.message("Done! Ignored " + str(ignored) + " bogus paths with < 20 points")
    open_file(directory)

def open_file(path):
    if platform.system() == "Windows":                                                      # if Windows
        os.startfile(path)                                                                  # open path in Explorer
    elif platform.system() == "Darwin":                                                     # if Mac
        subprocess.Popen(["open", path])                                                    # open path in Finder
    else:                                                                                   # if (assume) Linux
        subprocess.Popen(["xdg-open", path])                                                # open path with X-Window or fallback to default

def protected(function):                                                                    # try to allow undo operation (doesn't work sometimes)
    def p(*parms):                                                                          
        image=parms[0]
        pdb.gimp_image_undo_group_start(image)                                              # mark the image as dirty
        try:
            function(*parms)
        except Exception as e:
            print e.args[0]
            traceback.print_exc()
            pdb.gimp_message(e.args[0])
        pdb.gimp_image_undo_group_end(image)
        pdb.gimp_displays_flush()
    return p

register(                                                                                   # register function in GIMP
        "python_fu_export_as_pngs",
        "Export Separate Objects as PNGs...",
        "Export Separate Objects as PNGs...",
        "Brandon Phillips",
        "Brandon Phillips",
        "2020",
        "<Image>/Select/Export All Objects as PNGs...",
        '*',
        [(PF_STRING, "folder_name", "Folder Name", "output"),                               # prompt user for output folder name
         (PF_INT, "threshold_int", "Threshold (int)", "50"),                                # prompt user for threshold
         (PF_INT, "x_coord", "X Coord to Sample From", 10),                                 # prompt user for X coordinate
         (PF_INT, "y_coord", "Y Coord to Sample From", 10)],                                # prompt user for Y coordinate
        [],
        protected(getSelection)
)

register(                                                                                   # register function in GIMP
        "python_fu_export_as_pngs_with_sample",
        "Export Separate Objects as PNGs...",
        "Export Separate Objects as PNGs...",
        "Brandon Phillips",
        "Brandon Phillips",
        "2020",
        "<Image>/Select/Invert Selection and Export Objects as PNGs...",
        '*',
        [(PF_STRING, "folder_name", "Folder Name", "output")],                                # prompt user for output folder
        [],
        protected(deleteAndInvertSelection)
)
 
main()