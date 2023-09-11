"""Implementations of Qt Items."""


class TreeItem:
    """A single item in a tree.

    This class is used to represent a single item in a tree. This single item can have
    one column. It can have children, which are also TreeItems.

    The idea behind this class is to represent a dictionary as a tree. The zeroth
    element, of which all other elements are children, is the name of the experiment.
    Dictionary keys are then children of the experiment name, and dictionary values are
    children of the dictionary keys. We assume that all dictionary values are iterables.

    Example is adopted after:
    https://doc.qt.io/qtforpython-6/examples/example_widgets_itemviews_editabletreemodel.html
    """

    def __init__(self, experiment_name: str, parent: "TreeItem" = None):
        self.experiment_name = experiment_name
        self.parent_item = parent
        self.child_items = []

    def child(self, number: int) -> "TreeItem":
        """Return a child item depending on the index.

        :param number: Index of the child item.

        :return: Child item.
        """
        if number < 0 or number >= len(self.child_items):
            return None
        return self.child_items[number]

    def last_child(self) -> "TreeItem":
        """Return the last child item.

        :return: Last child item.
        """
        return self.child_items[-1] if self.child_items else None

    def child_count(self) -> int:
        """Return the number of child items.

        :return: Number of child items.
        """
        return len(self.child_items)

    def child_number(self) -> int:
        """Return the index of this child item in the parent's list of items.

        :return: Index of this child item in the parent's list of items.
        """
        if self.parent_item:
            return self.parent_item.child_items.index(self)
        return 0

    def column_count(self) -> int:
        """Return the number of columns that are used for the tree view."""
        return 1

    def data(self) -> str:
        """Return the column data of the item.

        :param column: Column index.

        :return: Column data.
        """
        return self.experiment_name

    def insert_children(self, position: int, count: int) -> bool:
        """Insert child(ren) into the tree.

        :param position: Position of the child item.
        :param count: Number of children to insert.
        :param columns: Number of columns to insert.
        """
        if position < 0 or position > len(self.child_items):
            return False

        for row in range(count):
            data = [None]
            item = TreeItem(data.copy(), self)
            self.child_items.insert(position, item)

        return True

    def parent(self):
        """Return the parent item."""
        return self.parent_item

    def remove_children(self, position: int, count: int) -> bool:
        """Remove child(ren) from the tree.

        :param position: Position of the child item.
        :param count: Number of children to remove.
        """
        if position < 0 or position + count > len(self.child_items):
            return False

        for row in range(count):
            self.child_items.pop(position)

        return True

    def set_data(self, value) -> bool:
        """Set the data of the item and return True if successful."""
        self.experiment_name = value
        return True

    def __repr__(self) -> str:
        return (
            f"<treeitem.TreeItem at 0x{id(self):x}, "
            f"{self.experiment_name}, "
            f"{len(self.child_items)} children>"
        )
