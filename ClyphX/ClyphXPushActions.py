"""
# Copyright (C) 2013-2015 Stray <stray411@hotmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# For questions regarding this module contact
# Stray <stray411@hotmail.com>
"""

# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-

from __future__ import with_statement
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from consts import *

UNWRITABLE_INDEXES = (17, 35, 53)
    
class ClyphXPushActions(ControlSurfaceComponent):
    __module__ = __name__
    __doc__ = ' Actions related to the Push control surface '
    
    def __init__(self, parent):
        ControlSurfaceComponent.__init__(self)
        self._parent = parent
	self._script = None
	self._ins_component = None
	self._note_editor = None
	
	
    def disconnect(self):
	self._script = None
	self._ins_component = None
	self._note_editor = None
	self._parent = None
	ControlSurfaceComponent.disconnect(self)		
	    
    
    def on_enabled_changed(self):
	pass
        

    def update(self):    
        pass    
    
    
    def set_script(self, push_script):
	""" Set the Push script to connect to and get necessary components. """
	self._script = push_script
	if self._script and self._script._components:
	    edit_comp_name = 'StepSeqComponent' if IS_LIVE_9_1 else 'NoteEditorComponent'
	    for c in self._script.components:
		comp_name = c.__class__.__name__
		if comp_name == 'InstrumentComponent':
		    self._ins_component = c
		elif comp_name == edit_comp_name:
		    self._note_editor = c
	
	
    def dispatch_action(self, track, xclip, ident, action, args):
	""" Dispatch action to proper action group handler. """
	if self._script:
	    if args.startswith('SCL') and self._ins_component:
		self._handle_scale_action(args.replace('SCL', '').strip(), xclip, ident)
	    elif args.startswith('SEQ') and self._note_editor:
		self._handle_sequence_action(args.replace('SEQ', '').strip())
	    elif args == 'DRINS' and self.song().view.selected_track.has_midi_input:
		with self._script._push_injector:
		    self._script._note_modes.selected_mode = 'instrument'
	    elif args.startswith('MSG'):
		self._display_message(args, xclip)
		
		
    def _display_message(self, args, xclip):
	""" Temporarily displays a message in Push's display
	Uses special handling to ensure that empty display spaces aren't written to. """
	note_as_caps = args.replace('MSG', '', 1).strip()
	note_len = len(note_as_caps)
	start_index = xclip.name.upper().find(note_as_caps)
	note_at_og_case = xclip.name[start_index:note_len+start_index]
	for i in UNWRITABLE_INDEXES:
	    if len(note_at_og_case) > i and note_at_og_case[i] != ' ':
		note_at_og_case = note_at_og_case[0:i] + ' ' + note_at_og_case[i:note_len]
		note_len += 1
	self._script.show_notification(note_at_og_case)
	    
		
    def _handle_scale_action(self, args, xclip, ident):
	""" Handles actions related to scale settings. """
	if args:
	    arg_array = args.split()
	    array_len = len(arg_array)
	    if arg_array[0] == 'INKEY':
		if array_len == 2 and arg_array[1] in KEYWORDS:
		    self._ins_component._scales.is_diatonic = KEYWORDS[arg_array[1]]
		else:
		    self._ins_component._scales.is_diatonic = not self._ins_component._scales.is_diatonic
	    elif arg_array[0] == 'FIXED':
		if array_len == 2 and arg_array[1] in KEYWORDS:
		    self._ins_component._scales.is_absolute = KEYWORDS[arg_array[1]]
		else:
		    self._ins_component._scales.is_absolute = not self._ins_component._scales.is_absolute	
	    elif arg_array[0] == 'ROOT' and array_len == 2:
		if arg_array[1] in NOTE_NAMES:
		    self._ins_component._scales.key_center = NOTE_NAMES.index(arg_array[1])
		elif arg_array[1] in ('<', '>'):
		    new_root = self._parent.get_adjustment_factor(arg_array[1]) + self._ins_component._scales.key_center
		    if new_root in range(12):
			self._ins_component._scales.key_center = new_root	    
	    elif arg_array[0] == 'TYPE' and array_len >= 2:
		if arg_array[1] in ('<', '>'):
		    if IS_LIVE_9_1:
			factor = self._parent.get_adjustment_factor(arg_array[1])
			if factor < 0:
			    for index in range(abs(factor)):
				self._ins_component._scales._modus_list.scrollable_list.scroll_down()
			else:
			    for index in range(factor):
				self._ins_component._scales._modus_list.scrollable_list.scroll_up()
		    else:
			new_scale = self._parent.get_adjustment_factor(arg_array[1]) + self._ins_component._scales._selected_modus
			if new_scale in range(len(self._ins_component._scales._modus_list)):
			    self._ins_component._scales._selected_modus = new_scale
		else:
		    scale_type = args.replace('TYPE', '').strip()
		    if IS_LIVE_9_1:
			for index in range(len(self._ins_component._scales._modus_list.scrollable_list.items)):
			    modus = self._ins_component._scales._modus_list.scrollable_list.items[index]
			    if modus.content.name.upper() == scale_type:
				self._ins_component._scales._modus_list.scrollable_list._set_selected_item_index(index)
				break
		    else:
			for modus in self._ins_component._scales._modus_list:
			    if modus.name.upper() == scale_type:
				self._ins_component._scales._selected_modus = self._ins_component._scales._modus_list.index(modus)
				break
	    elif arg_array[0] == 'OCT' and array_len >= 2 and arg_array[1] in ('<', '>'):
		if arg_array[1] == '<':
		    if IS_LIVE_9_1:
			self._ins_component._slider.scroll_page_down()
		    else:
			self._ins_component._scroll_octave_down()
		else:
		    if IS_LIVE_9_1:
			self._ins_component._slider.scroll_page_up()
		    else:
			self._ins_component._scroll_octave_up()
	    else:
		if array_len == 6:
		    self._recall_scale_settings(arg_array)     
	    self._update_scale_display_and_buttons()
	else:
	    self._capture_scale_settings(xclip, ident)
	
		
    def _capture_scale_settings(self, xclip, ident):
	""" Captures scale settings and writes them to X-Clip's name. """
	if type(xclip) is Live.Clip.Clip:
	    root = str(self._ins_component._scales.key_center)
	    if IS_LIVE_9_1:
		scl_type = str(self._ins_component._scales._modus_list.scrollable_list._get_selected_item_index())
		octave = str(int(self._ins_component._slider._slideable.position))
	    else:
		scl_type = str(self._ins_component._scales._selected_modus)
		octave = str(self._ins_component._octave_index)
	    fixed = str(self._ins_component._scales.is_absolute)
	    inkey = str(self._ins_component._scales.is_diatonic)
	    orient = str(self._ins_component._scales._presets._get_selected_mode())
	    xclip.name = ident + ' Push SCL ' + root + ' ' + scl_type + ' ' + octave + ' ' + fixed + ' ' + inkey + ' ' + orient
	    
	    
    def _recall_scale_settings(self, arg_array):
	""" Recalls scale settings from X-Trigger name. """
	try:
	    self._ins_component._scales.key_center = int(arg_array[0])
	    if IS_LIVE_9_1:
		self._ins_component._scales._modus_list.scrollable_list._set_selected_item_index(int(arg_array[1]))
		#self._ins_component._slider._slideable.position = int(arg_array[2]) -- Octave recall doesn't work correctly with 9.1
		self._ins_component._slider.update()
	    else:
		self._ins_component._scales._selected_modus = int(arg_array[1])
		self._ins_component._octave_index = int(arg_array[2])
	    self._ins_component._scales.is_absolute = arg_array[3] == 'TRUE'
	    self._ins_component._scales.is_diatonic = arg_array[4] == 'TRUE'
	    self._ins_component._scales._presets._set_selected_mode(arg_array[5].lower())
	    self._ins_component._scales._presets.push_mode(arg_array[5].lower())
	except: pass
	    
	
    def _update_scale_display_and_buttons(self):
	""" Updates Push's scale display and buttons to indicate current settings. """
	with self._script._push_injector:
	    self._ins_component._scales._update_data_sources()
	    self._ins_component._scales.notify_scales_changed()
	    self._ins_component._scales.update()
	    if not IS_LIVE_9_1:
		self._ins_component._scales._modus_scroll.update()
	    
	
    def _handle_sequence_action(self, args):
	""" Handle note actions related to the note currently being sequenced. """
	if IS_LIVE_9_1:
	    note = self._note_editor._note_editor.editing_note
	    if self._note_editor._detail_clip and note != None:
		self._parent._clip_actions.do_clip_note_action(self._note_editor._detail_clip, None, None, '', 'NOTES' + str(note) + ' ' + args)
	else:
	    if self._note_editor._sequencer_clip and self._note_editor._clip_notes:
		note_name = self._note_number_to_name(self._note_editor._clip_notes[0][0])
		self._parent._clip_actions.do_clip_note_action(self._note_editor._sequencer_clip, None, None, '', 'NOTES' + note_name + ' ' + args)
	    
	    
    def _note_number_to_name(self, number):
	""" Returns the note name for the given note number. """
	return str(NOTE_NAMES[number % 12]) + str((number / 12) - 2)
    
# local variables:
# tab-width: 4