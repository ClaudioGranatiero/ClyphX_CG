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
from consts import NOTE_NAMES

class MacrobatPushRack(ControlSurfaceComponent):
    __module__ = __name__
    __doc__ = ' Sets up Macros 1 and 2 to control Push root note and scale type respectively. '    

    def __init__(self, parent, rack):
        ControlSurfaceComponent.__init__(self)
	self._parent = parent
	self._rack = rack
	self._script = None
	self._push_ins = self._connect_to_push()
	self.setup_device()
	
	
    def disconnect(self):
	self.remove_macro_listeners()
	self._rack = None
	self._script = None
	self._push_ins = None
	self._parent = None
	ControlSurfaceComponent.disconnect(self)
		
	    
    def on_enabled_changed(self):
        pass
        

    def update(self):    
        self._push_ins = self._connect_to_push()
	
		
    def setup_device(self):
	""" Rack names needs to start with nK SCL and Push needs to be selected as a control surface. """
	self._push_ins = self._connect_to_push()
	self.remove_macro_listeners()
	if self._rack:
	    if self._rack.parameters[1].is_enabled:
		self._rack.parameters[1].add_value_listener(self._on_macro_one_value)
	    if self._rack.parameters[2].is_enabled:
		self._rack.parameters[2].add_value_listener(self._on_macro_two_value)
	    self._parent.schedule_message(1, self._update_rack_name)

		
    def _connect_to_push(self):
	""" Attempt to connect to Push. """
	for script in self._parent._control_surfaces():
	    script_name = script.__class__.__name__  
	    if script_name == 'Push':
		self._script = script
		for c in script.components:
		    comp_name = c.__class__.__name__
		    if comp_name == 'InstrumentComponent':
			return c
	return None
    
		
    def _on_macro_one_value(self):
	""" Set Push root note and update rack name. """
	if self._push_ins:
	    new_root = self.scale_macro_value_to_param(self._rack.parameters[1], 12)
	    if new_root != self._push_ins._scales.key_center:
		with self._script._push_injector:
		    self._push_ins._scales._update_data_sources()
		    self._push_ins._scales.key_center = new_root
		    self._push_ins._scales.notify_scales_changed()
		self._parent.schedule_message(1, self._update_rack_name)
    
    
    def _on_macro_two_value(self):
	""" Set Push scale type and update rack name. """
	if self._push_ins:
	    new_type = self.scale_macro_value_to_param(self._rack.parameters[2], len(self._push_ins._scales._modus_list))
	    if new_type != self._push_ins._scales._selected_modus:
		with self._script._push_injector:
		    self._push_ins._scales._update_data_sources()
		    self._push_ins._scales._selected_modus = new_type
		    self._push_ins._scales.notify_scales_changed()
		self._parent.schedule_message(1, self._update_rack_name)
	
	
    def _update_rack_name(self):
	""" Update rack name to reflect selected root note and scale type. """
	if self._rack and self._push_ins:
	    self._rack.name = 'nK SCL - ' + str(NOTE_NAMES[self._push_ins._scales.key_center]) + ' - ' + str(self._push_ins._scales._modus_list[self._push_ins._scales._selected_modus].name)
	
    
    def scale_macro_value_to_param(self, macro, hi_value):
	""" Scale the value of the macro to the Push parameter being controlled. """
	return int((hi_value / 128.0) * macro.value)
    
    
    def remove_macro_listeners(self):
	""" Remove listeners """
	if self._rack:
	    if self._rack.parameters[1].value_has_listener(self._on_macro_one_value):
		self._rack.parameters[1].remove_value_listener(self._on_macro_one_value)
	    if self._rack.parameters[2].value_has_listener(self._on_macro_two_value):
		self._rack.parameters[2].remove_value_listener(self._on_macro_two_value)
	
		
# local variables:
# tab-width: 4