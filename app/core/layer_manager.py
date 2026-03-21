"""
Layer Manager module - Manages all layers and layer groups.

Handles layer creation, deletion, ordering, grouping, and overlay display.
"""

from typing import List, Optional, Union, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor, QImage, QPainter

from app.core.layer import Layer, LayerGroup, DrawingElement


class LayerManager(QObject):
    """
    Manages all layers and layer groups in the application.
    
    Emits signals when layers change, allowing UI components to update.
    """
    
    layer_added = pyqtSignal(object)  # Layer or LayerGroup
    layer_removed = pyqtSignal(str)  # Layer ID
    layer_changed = pyqtSignal(str)  # Layer ID
    current_layer_changed = pyqtSignal(object)  # Current layer
    layers_reordered = pyqtSignal()
    overlay_visibility_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.layers: List[Union[Layer, LayerGroup]] = []
        self.current_layer: Optional[Layer] = None
        self.overlay_visible = True
        self._layer_counter = 0
        
        # Create default layer
        self._create_default_layer()
    
    def _create_default_layer(self):
        """Create the initial default layer."""
        layer = self.create_layer("Background")
        layer.color = QColor('#3498db')
    
    def create_layer(self, name: str = None) -> Layer:
        """Create a new layer and add it to the top."""
        self._layer_counter += 1
        if name is None:
            name = f"Layer {self._layer_counter}"
        
        layer = Layer(name)
        layer.color = self._get_random_color()
        
        # Add to top of stack
        self.layers.insert(0, layer)
        self.current_layer = layer
        
        self.layer_added.emit(layer)
        self.current_layer_changed.emit(layer)
        
        return layer
    
    def create_group(self, name: str = None) -> LayerGroup:
        """Create a new layer group."""
        self._layer_counter += 1
        if name is None:
            name = f"Group {self._layer_counter}"
        
        group = LayerGroup(name)
        self.layers.insert(0, group)
        
        self.layer_added.emit(group)
        
        return group
    
    def _get_random_color(self) -> QColor:
        """Generate a random color for layer identification."""
        colors = [
            '#E74C3C', '#3498DB', '#2ECC71', '#F39C12',
            '#9B59B6', '#1ABC9C', '#E67E22', '#34495E',
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
        ]
        import random
        return QColor(random.choice(colors))
    
    def get_layer(self, layer_id: str) -> Optional[Layer]:
        """Get a layer by ID (searches recursively)."""
        for item in self.layers:
            if isinstance(item, Layer) and item.id == layer_id:
                return item
            elif isinstance(item, LayerGroup):
                for layer in item.layers:
                    if layer.id == layer_id:
                        return layer
        return None
    
    def get_current_layer(self) -> Optional[Layer]:
        """Get the current active layer."""
        return self.current_layer
    
    def set_current_layer(self, layer: Layer):
        """Set the current active layer."""
        if layer and not layer.locked:
            self.current_layer = layer
            self.current_layer_changed.emit(layer)
    
    def set_current_layer_by_id(self, layer_id: str) -> bool:
        """Set current layer by ID."""
        layer = self.get_layer(layer_id)
        if layer:
            self.set_current_layer(layer)
            return True
        return False
    
    def remove_layer(self, layer: Layer) -> bool:
        """Remove a layer from the manager."""
        # Remove from top level
        if layer in self.layers:
            self.layers.remove(layer)
            self.layer_removed.emit(layer.id)
            
            # Update current layer if needed
            if self.current_layer == layer:
                self.current_layer = self.layers[0] if self.layers else None
                if isinstance(self.current_layer, Layer):
                    self.current_layer_changed.emit(self.current_layer)
            
            return True
        
        # Search in groups
        for item in self.layers:
            if isinstance(item, LayerGroup) and layer in item.layers:
                item.remove_layer(layer)
                self.layer_removed.emit(layer.id)
                return True
        
        return False
    
    def remove_layer_by_id(self, layer_id: str) -> bool:
        """Remove a layer by ID."""
        layer = self.get_layer(layer_id)
        if layer:
            return self.remove_layer(layer)
        return False
    
    def delete_layer(self, layer: Layer) -> bool:
        """Delete a layer (alias for remove)."""
        return self.remove_layer(layer)
    
    def clear_layer(self, layer: Layer):
        """Clear all content from a layer."""
        if not layer.locked:
            layer.clear()
            self.layer_changed.emit(layer.id)
    
    def move_layer_up(self, layer: Layer) -> bool:
        """Move layer up in stack (visually forward)."""
        if layer in self.layers:
            idx = self.layers.index(layer)
            if idx > 0:
                self.layers.insert(idx - 1, self.layers.pop(idx))
                self.layers_reordered.emit()
                return True
        return False
    
    def move_layer_down(self, layer: Layer) -> bool:
        """Move layer down in stack (visually backward)."""
        if layer in self.layers:
            idx = self.layers.index(layer)
            if idx < len(self.layers) - 1:
                self.layers.insert(idx + 1, self.layers.pop(idx))
                self.layers_reordered.emit()
                return True
        return False
    
    def add_to_group(self, layer: Layer, group: LayerGroup):
        """Add a layer to a group."""
        if layer in self.layers:
            self.layers.remove(layer)
        group.add_layer(layer)
        self.layers_reordered.emit()
    
    def remove_from_group(self, layer: Layer, group: LayerGroup) -> bool:
        """Remove a layer from a group."""
        if group.remove_layer(layer):
            # Add back to top level
            self.layers.insert(0, layer)
            self.layers_reordered.emit()
            return True
        return False
    
    def set_overlay_visible(self, visible: bool):
        """Set whether overlay view is visible."""
        self.overlay_visible = visible
        self.overlay_visibility_changed.emit(visible)
    
    def toggle_overlay(self):
        """Toggle overlay view visibility."""
        self.set_overlay_visible(not self.overlay_visible)
    
    def get_all_layers_flat(self) -> List[Layer]:
        """Get all layers as a flat list (including from groups)."""
        result = []
        for item in self.layers:
            if isinstance(item, Layer):
                result.append(item)
            elif isinstance(item, LayerGroup):
                if item.expanded:
                    result.extend(item.layers)
                else:
                    result.append(item)  # Group collapsed
        return result
    
    def render_all(self, painter: QPainter, include_overlay: bool = True):
        """Render all visible layers to the painter."""
        # Render from bottom to top
        for item in reversed(self.layers):
            if isinstance(item, Layer):
                if item.visible:
                    item.render(painter)
            elif isinstance(item, LayerGroup):
                if item.visible:
                    for layer in item.layers:
                        if layer.visible:
                            layer.render(painter)
    
    def render_overlay(self, painter: QPainter, current_only: bool = True):
        """Render overlay view showing layer structure."""
        if not self.overlay_visible:
            return
        
        painter.save()
        painter.setOpacity(0.3)
        
        # Render all layers except current (or all)
        for item in reversed(self.layers):
            if isinstance(item, Layer):
                if item != self.current_layer or not current_only:
                    item.render(painter)
            elif isinstance(item, LayerGroup):
                for layer in item.layers:
                    if layer != self.current_layer or not current_only:
                        layer.render(painter)
        
        painter.restore()
    
    def get_layer_count(self) -> int:
        """Get total number of layers."""
        count = 0
        for item in self.layers:
            if isinstance(item, Layer):
                count += 1
            elif isinstance(item, LayerGroup):
                count += len(item.layers)
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert layer manager state to dictionary."""
        return {
            'layers': [
                l.to_dict() if isinstance(l, Layer) else l.to_dict()
                for l in self.layers
            ],
            'current_layer_id': self.current_layer.id if self.current_layer else None,
            'overlay_visible': self.overlay_visible,
            'layer_counter': self._layer_counter,
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load layer manager state from dictionary."""
        self.layers.clear()
        
        for item_data in data.get('layers', []):
            if item_data.get('type') == 'group':
                group = LayerGroup.from_dict(item_data)
                self.layers.append(group)
            else:
                layer = Layer.from_dict(item_data)
                self.layers.append(layer)
        
        current_id = data.get('current_layer_id')
        if current_id:
            self.current_layer = self.get_layer(current_id)
        
        self._layer_counter = data.get('layer_counter', len(self.layers))
        self.overlay_visible = data.get('overlay_visible', True)
        
        if not self.current_layer and self.layers:
            for item in self.layers:
                if isinstance(item, Layer):
                    self.current_layer = item
                    break
                elif isinstance(item, LayerGroup) and item.layers:
                    self.current_layer = item.layers[0]
                    break
        
        self.layers_reordered.emit()
