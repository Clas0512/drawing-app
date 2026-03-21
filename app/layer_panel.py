"""
Layer Panel module - Widget for managing layers.

Provides UI for layer visibility, locking, ordering, grouping,
and overlay view control.
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QCheckBox, QSlider,
    QGroupBox, QFrame, QColorDialog, QInputDialog, QMenu,
    QAction, QToolButton, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QIcon, QPainter, QBrush, QPen

from app.core.layer_manager import LayerManager
from app.core.layer import Layer, LayerGroup


class LayerItemWidget(QWidget):
    """Custom widget for displaying layer info in list."""
    
    visibility_changed = pyqtSignal(str, bool)  # layer_id, visible
    lock_changed = pyqtSignal(str, bool)  # layer_id, locked
    
    def __init__(self, layer: Layer, parent=None):
        super().__init__(parent)
        self.layer = layer
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Color indicator
        self.color_label = QLabel()
        self.color_label.setFixedSize(16, 16)
        self.color_label.setStyleSheet(
            f"background-color: {layer.color.name()}; border: 1px solid #888; border-radius: 2px;"
        )
        layout.addWidget(self.color_label)
        
        # Visibility checkbox
        self.visibility_cb = QCheckBox()
        self.visibility_cb.setChecked(layer.visible)
        self.visibility_cb.setToolTip("Toggle visibility")
        self.visibility_cb.stateChanged.connect(self._on_visibility_changed)
        layout.addWidget(self.visibility_cb)
        
        # Lock checkbox
        self.lock_cb = QCheckBox()
        self.lock_cb.setChecked(layer.locked)
        self.lock_cb.setToolTip("Toggle lock")
        self.lock_cb.setText("🔒" if layer.locked else "🔓")
        self.lock_cb.stateChanged.connect(self._on_lock_changed)
        layout.addWidget(self.lock_cb)
        
        # Layer name
        self.name_label = QLabel(layer.name)
        self.name_label.setMinimumWidth(100)
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
        # Element count
        self.count_label = QLabel(f"({len(layer.elements)})")
        self.count_label.setStyleSheet("color: #888;")
        layout.addWidget(self.count_label)
    
    def _on_visibility_changed(self, state):
        """Handle visibility change."""
        self.layer.set_visible(state == Qt.Checked)
        self.visibility_changed.emit(self.layer.id, state == Qt.Checked)
    
    def _on_lock_changed(self, state):
        """Handle lock change."""
        self.layer.set_locked(state == Qt.Checked)
        self.lock_cb.setText("🔒" if state == Qt.Checked else "🔓")
        self.lock_changed.emit(self.layer.id, state == Qt.Checked)
    
    def update_display(self):
        """Update the display with current layer state."""
        self.visibility_cb.setChecked(self.layer.visible)
        self.lock_cb.setChecked(self.layer.locked)
        self.lock_cb.setText("🔒" if self.layer.locked else "🔓")
        self.name_label.setText(self.layer.name)
        self.count_label.setText(f"({len(self.layer.elements)})")
        self.color_label.setStyleSheet(
            f"background-color: {self.layer.color.name()}; border: 1px solid #888; border-radius: 2px;"
        )


class LayerPanel(QWidget):
    """
    Panel widget for managing layers.
    
    Provides controls for:
    - Adding/removing layers
    - Layer visibility and locking
    - Layer ordering
    - Grouping layers
    - Overlay view toggle
    """
    
    def __init__(self, layer_manager: LayerManager):
        super().__init__()
        self.layer_manager = layer_manager
        
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
        
        self._init_ui()
        self._connect_signals()
        self._refresh_layers()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Layers")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Toolbar buttons
        toolbar_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("+ Layer")
        self.add_btn.setToolTip("Add new layer")
        self.add_btn.clicked.connect(self._add_layer)
        toolbar_layout.addWidget(self.add_btn)
        
        self.add_group_btn = QPushButton("+ Group")
        self.add_group_btn.setToolTip("Add new group")
        self.add_group_btn.clicked.connect(self._add_group)
        toolbar_layout.addWidget(self.add_group_btn)
        
        self.overlay_btn = QPushButton("👁 Overlay")
        self.overlay_btn.setToolTip("Toggle overlay view")
        self.overlay_btn.setCheckable(True)
        self.overlay_btn.setChecked(True)
        self.overlay_btn.clicked.connect(self._toggle_overlay)
        toolbar_layout.addWidget(self.overlay_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Layer list
        self.layer_list = QListWidget()
        self.layer_list.setDragDropMode(QListWidget.InternalMove)
        self.layer_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.layer_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.layer_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.layer_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.layer_list)
        
        # Layer controls
        controls_group = QGroupBox("Layer Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Opacity slider
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("100%")
        opacity_layout.addWidget(self.opacity_label)
        controls_layout.addLayout(opacity_layout)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.up_btn = QPushButton("↑ Up")
        self.up_btn.clicked.connect(self._move_up)
        actions_layout.addWidget(self.up_btn)
        
        self.down_btn = QPushButton("↓ Down")
        self.down_btn.clicked.connect(self._move_down)
        actions_layout.addWidget(self.down_btn)
        
        controls_layout.addLayout(actions_layout)
        
        actions_layout2 = QHBoxLayout()
        
        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.clicked.connect(self._delete_layer)
        actions_layout2.addWidget(self.delete_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_layer)
        actions_layout2.addWidget(self.clear_btn)
        
        controls_layout.addLayout(actions_layout2)
        
        layout.addWidget(controls_group)
    
    def _connect_signals(self):
        """Connect layer manager signals."""
        self.layer_manager.layer_added.connect(self._refresh_layers)
        self.layer_manager.layer_removed.connect(self._refresh_layers)
        self.layer_manager.layer_changed.connect(self._refresh_layers)
        self.layer_manager.layers_reordered.connect(self._refresh_layers)
        self.layer_manager.current_layer_changed.connect(self._on_current_changed)
    
    def _refresh_layers(self):
        """Refresh the layer list display."""
        self.layer_list.clear()
        
        for item in self.layer_manager.layers:
            if isinstance(item, Layer):
                self._add_layer_to_list(item)
            elif isinstance(item, LayerGroup):
                self._add_group_to_list(item)
    
    def _add_layer_to_list(self, layer: Layer):
        """Add a layer item to the list."""
        list_item = QListWidgetItem()
        list_item.setData(Qt.UserRole, layer.id)
        
        # Set background color for current layer
        if layer == self.layer_manager.get_current_layer():
            list_item.setBackground(QColor(200, 230, 255))
        
        self.layer_list.addItem(list_item)
        
        # Create custom widget
        widget = LayerItemWidget(layer)
        widget.visibility_changed.connect(self._on_visibility_changed)
        widget.lock_changed.connect(self._on_lock_changed)
        list_item.setSizeHint(widget.sizeHint())
        self.layer_list.setItemWidget(list_item, widget)
    
    def _add_group_to_list(self, group: LayerGroup):
        """Add a group item to the list."""
        # Group header
        list_item = QListWidgetItem()
        list_item.setData(Qt.UserRole, group.id)
        list_item.setText(f"📁 {group.name} ({len(group.layers)} layers)")
        list_item.setFlags(list_item.flags() & ~Qt.ItemIsDragEnabled)
        
        if not group.visible:
            list_item.setForeground(QColor(150, 150, 150))
        
        self.layer_list.addItem(list_item)
        
        # Add layers if expanded
        if group.expanded:
            for layer in group.layers:
                sub_item = QListWidgetItem()
                sub_item.setData(Qt.UserRole, layer.id)
                sub_item.setText(f"    {layer.name}")
                self.layer_list.addItem(sub_item)
    
    def _on_selection_changed(self):
        """Handle layer selection change."""
        items = self.layer_list.selectedItems()
        if items:
            layer_id = items[0].data(Qt.UserRole)
            if layer_id:
                self.layer_manager.set_current_layer_by_id(layer_id)
    
    def _on_current_changed(self, layer):
        """Handle current layer change."""
        self._refresh_layers()
    
    def _on_item_double_clicked(self, item):
        """Handle double-click on layer (rename)."""
        layer_id = item.data(Qt.UserRole)
        layer = self.layer_manager.get_layer(layer_id)
        if layer:
            new_name, ok = QInputDialog.getText(
                self, "Rename Layer", "Layer name:",
                text=layer.name
            )
            if ok and new_name:
                layer.set_name(new_name)
                self._refresh_layers()
    
    def _show_context_menu(self, pos):
        """Show context menu for layer."""
        item = self.layer_list.itemAt(pos)
        if item:
            layer_id = item.data(Qt.UserRole)
            layer = self.layer_manager.get_layer(layer_id)
            
            if layer:
                menu = QMenu(self)
                
                # Rename action
                rename_action = QAction("Rename", self)
                rename_action.triggered.connect(lambda: self._on_item_double_clicked(item))
                menu.addAction(rename_action)
                
                # Change color action
                color_action = QAction("Change Color", self)
                color_action.triggered.connect(lambda: self._change_color(layer))
                menu.addAction(color_action)
                
                menu.addSeparator()
                
                # Delete action
                delete_action = QAction("Delete", self)
                delete_action.triggered.connect(self._delete_layer)
                menu.addAction(delete_action)
                
                # Clear action
                clear_action = QAction("Clear Content", self)
                clear_action.triggered.connect(self._clear_layer)
                menu.addAction(clear_action)
                
                menu.exec_(self.layer_list.mapToGlobal(pos))
    
    def _change_color(self, layer: Layer):
        """Change layer color."""
        color = QColorDialog.getColor(layer.color, self, "Choose Layer Color")
        if color.isValid():
            layer.set_color(color)
            self._refresh_layers()
    
    def _add_layer(self):
        """Add a new layer."""
        name, ok = QInputDialog.getText(
            self, "New Layer", "Layer name:",
            text=f"Layer {self.layer_manager._layer_counter + 1}"
        )
        if ok:
            self.layer_manager.create_layer(name if name else None)
    
    def _add_group(self):
        """Add a new group."""
        name, ok = QInputDialog.getText(
            self, "New Group", "Group name:",
            text=f"Group {self.layer_manager._layer_counter + 1}"
        )
        if ok:
            self.layer_manager.create_group(name if name else None)
    
    def _toggle_overlay(self, checked):
        """Toggle overlay view."""
        self.layer_manager.set_overlay_visible(checked)
    
    def _on_visibility_changed(self, layer_id: str, visible: bool):
        """Handle visibility change."""
        self._refresh_layers()
    
    def _on_lock_changed(self, layer_id: str, locked: bool):
        """Handle lock change."""
        self._refresh_layers()
    
    def _on_opacity_changed(self, value):
        """Handle opacity change."""
        self.opacity_label.setText(f"{value}%")
        current = self.layer_manager.get_current_layer()
        if current:
            current.set_opacity(value / 100.0)
            self.layer_manager.layer_changed.emit(current.id)
    
    def _move_up(self):
        """Move current layer up."""
        current = self.layer_manager.get_current_layer()
        if current:
            self.layer_manager.move_layer_up(current)
    
    def _move_down(self):
        """Move current layer down."""
        current = self.layer_manager.get_current_layer()
        if current:
            self.layer_manager.move_layer_down(current)
    
    def _delete_layer(self):
        """Delete current layer."""
        current = self.layer_manager.get_current_layer()
        if current:
            reply = QMessageBox.question(
                self, "Delete Layer",
                f"Are you sure you want to delete '{current.name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.layer_manager.remove_layer(current)
    
    def _clear_layer(self):
        """Clear current layer content."""
        current = self.layer_manager.get_current_layer()
        if current:
            reply = QMessageBox.question(
                self, "Clear Layer",
                f"Clear all content from '{current.name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.layer_manager.clear_layer(current)
