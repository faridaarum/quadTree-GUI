import mysql.connector
import numpy as np
import math
from matplotlib.patches import Rectangle
class Point:
    def __init__(self, x, y, id=None):
        self.x = x
        self.y = y
        self.id = id

    def distanceToCenter(self, center):
        return math.sqrt((center.x - self.x) ** 2 + (center.y - self.y) ** 2)

    def saveToMysql(self):
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='',
            database='qtree'
        )

        cursor = conn.cursor()

        if self.id is None:
            cursor.execute('INSERT INTO point (x, y) VALUES (%s, %s)', (self.x, self.y))
            self.id = cursor.lastrowid
        else:
            cursor.execute('UPDATE point SET x=%s, y=%s WHERE id=%s', (self.x, self.y, self.id))

        conn.commit()
        conn.close()

    def loadFromMysql(self, id):
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='',
            database='qtree'
        )

        cursor = conn.cursor()

        cursor.execute('SELECT x, y FROM point WHERE id=%s', (id,))
        result = cursor.fetchone()

        if result is not None:
            self.x = result[0]
            self.y = result[1]

        conn.close()

class Rectangle:
    def __init__(self, center, width, height):
        self.center = center
        self.width = width
        self.height = height
        self.west = center.x - width
        self.east = center.x + width
        self.north = center.y - height
        self.south = center.y + height

    def containsPoint(self, point):
        return (self.west <= point.x < self.east and
                self.north <= point.y < self.south)

    def intersects(self, range):
        return not (range.west > self.east or
                    range.east < self.west or
                    range.north > self.south or
                    range.south < self.north)

    def draw(self, canvas):
        # Draw a rectangle on the canvas based on the boundary
        x1 = self.center.x - self.width
        y1 = self.center.y - self.height
        x2 = self.center.x + self.width
        y2 = self.center.y + self.height
        canvas.create_rectangle(x1, y1, x2, y2)

    def get_bbox(self):
        """Return a bounding box for the rectangle."""

        min_x = self.center.x - self.width / 2
        max_x = self.center.x + self.width / 2
        min_y = self.center.y - self.height / 2
        max_y = self.center.y + self.height / 2

        return Rectangle(Point(min_x, min_y), max_x - min_x, max_y - min_y)


class QuadTree:
    def __init__(self, boundary, capacity=4):
        self.boundary = boundary
        self.capacity = capacity
        self.points = []
        self.divided = False
        self.canvas_id = None

    def insert(self, point):
        # if the point is in the range of current quadTree
        if not self.boundary.containsPoint(point):
            return False

        # if has not reached capacaity
        if len(self.points) < self.capacity:
            self.points.append(point)
            return True

        if not self.divided:
            self.divide()

        if self.nw.insert(point):
            return True
        elif self.ne.insert(point):
            return True
        elif self.sw.insert(point):
            return True
        elif self.se.insert(point):
            return True

        return False

    def queryRange(self, range):
        found_points = []

        if not self.boundary.intersects(range):
            return []

        for point in self.points:
            if range.containsPoint(point):
                found_points.append(point)

        if self.divided:
            found_points.extend(self.nw.queryRange(range))
            found_points.extend(self.ne.queryRange(range))
            found_points.extend(self.sw.queryRange(range))
            found_points.extend(self.se.queryRange(range))

        return found_points

    def queryRadius(self, range, center):
        found_points = []

        if not self.boundary.intersects(range):
            return []

        for point in self.points:
            if range.containsPoint(point) and point.distanceToCenter(center) <= range.width:
                found_points.append(point)

        if self.divided:
            found_points.extend(self.nw.queryRadius(range, center))
            found_points.extend(self.ne.queryRadius(range, center))
            found_points.extend(self.sw.queryRadius(range, center))
            found_points.extend(self.se.queryRadius(range, center))

        return found_points

    def divide(self):
        center_x = self.boundary.center.x
        center_y = self.boundary.center.y
        new_width = self.boundary.width / 2
        new_height = self.boundary.height / 2

        nw = Rectangle(Point(center_x - new_width, center_y - new_height), new_width, new_height)
        self.nw = QuadTree(nw)

        ne = Rectangle(Point(center_x + new_width, center_y - new_height), new_width, new_height)
        self.ne = QuadTree(ne)

        sw = Rectangle(Point(center_x - new_width, center_y + new_height), new_width, new_height)
        self.sw = QuadTree(sw)

        se = Rectangle(Point(center_x + new_width, center_y + new_height), new_width, new_height)
        self.se = QuadTree(se)

        self.divided = True

    def __len__(self):
        count = len(self.points)
        if self.divided:
            count += len(self.nw) + len(self.ne) + len(self.sw) + len(self.se)

        return count

    def draw(self, canvas):
        self.boundary.draw(canvas)

        # Assign a unique tag for each QuadTree node
        self.canvas_object_id = canvas.create_rectangle(self.boundary.center.x - self.boundary.width,
                                self.boundary.center.y - self.boundary.height,
                                self.boundary.center.x + self.boundary.width,
                                self.boundary.center.y + self.boundary.height,
                                tags=("quadtree",))

        if self.divided:
            self.nw.draw(canvas)
            self.ne.draw(canvas)
            self.se.draw(canvas)
            self.sw.draw(canvas)

        return self.canvas_id

    def delete_from_canvas(self, canvas):
        if self.canvas_id:
            canvas.delete(self.canvas_id)

class QuadTreeDrawer:
    def __init__(self, canvas, quadtree, points):
        self.canvas = canvas
        self.quadtree = quadtree
        self.points = points

        # Store a list of all of the graphics objects that are associated
        # with the QuadTree.
        self.graphics_objects = []

    def draw_quadtree(self):
        # Delete all of the existing graphics objects.
        for obj in self.graphics_objects:
            self.canvas.delete(obj)

        # Redraw the QuadTree nodes.
        self.draw_node(self.quadtree.root)

    def draw_node(self, node):
        # Create a graphics object for the node's rectangle.
        rectangle = self.canvas.create_rectangle(node.bbox, outline="black", tags=("quadtree"))
        self.graphics_objects.append(rectangle)

        # Create graphics objects for the points inside the node.
        for point in node.points:
            circle = self.canvas.create_oval(point.x - 2, point.y - 2, point.x + 2, point.y + 2, fill="red")
            self.graphics_objects.append(circle)

        # Draw the child nodes, if any.
        for child in node.children:
            self.draw_node(child)

    def delete_quadtree(self):
        # Delete all of the graphics objects that are associated with the QuadTree.
        for obj in self.graphics_objects:
            self.canvas.delete(obj)

        # Delete the QuadTree object itself.
        del self.quadtree

    def print_quadtree_tags(self):
        # Retrieve all items tagged as "quadtree" from the canvas
        quadtree_tags = self.canvas.find_withtag("quadtree")

        if quadtree_tags:
            print("Tags for QuadTree nodes:")
            for tag in quadtree_tags:
                item_tags = self.canvas.gettags(tag)
                print(f"Item ID {tag}: Tags - {item_tags}")
        else:
            print("No QuadTree nodes found on the canvas.")



