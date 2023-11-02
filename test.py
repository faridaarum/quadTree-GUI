import mysql.connector
import tkinter as tk
import matplotlib.pyplot as plt
from connection import Point, Rectangle, QuadTree, QuadTreeDrawer

# Create a new connection to the database.
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='qtree'
)

width = 200
height = 200

# Create a cursor.
cursor = conn.cursor()

data_center_x = []
data_center_y = []
data_points = []
right_side = 0
left_side = 0
bottom_side = 0
up_side = 0

# Global variables for mouse interaction
prev_x, prev_y = None, None
clicked_point = None
quadtree_object_id = None


def clear_canvas():
    canvas.delete()

def on_button_press(event):
    # Store the initial position when the mouse button is pressed
    global prev_x, prev_y
    prev_x, prev_y = event.x, event.y

def on_button_release(event):
    global quadtree_object_id
    # Get all items in the canvas
    all_items = canvas.find_all()
    quadtree = []

    # Get the current position of the rectangle after the mouse button is released
    # Get the current position and size of the updated rectangle after mouse release
    new_coords = canvas.coords(rectangle)
    new_center_x = (new_coords[0] + new_coords[2]) / 2
    new_center_y = (new_coords[1] + new_coords[3]) / 2
    rect_width = abs(new_coords[0] - new_coords[2]) / 2
    rect_height = abs(new_coords[1] - new_coords[3]) / 2
    print("New Center rectangle:", new_center_x, new_center_y)

    # Menambahkan nilai baru ke dalam list
    data_center_x.append(new_center_x)
    data_center_y.append(new_center_y)

    # Hapus semua oval sebelum menampilkan yang baru
    for item in canvas.find_all():
        if canvas.type(item) == 'oval':
            canvas.delete(item)

    print_quadtree_tags()

    # Query database for all points within the rectangle
    right_side = new_center_x + rect_width
    left_side = new_center_x - rect_width
    bottom_side = new_center_y - rect_height
    up_side = new_center_y + rect_height

    query = 'SELECT id, x, y FROM point WHERE x BETWEEN {} AND {} AND y BETWEEN {} AND {}'.format(left_side,
                                                                                                      right_side,
                                                                                                      bottom_side,
                                                                                                      up_side)
    cursor.execute(query)
    data_points = cursor.fetchall()

    domain = Rectangle(Point(new_center_x, new_center_y), rect_width, rect_height)
    qtree = QuadTree(domain, 4)

    for point in data_points:
        oval = canvas.create_oval(point[1] - 2, point[2] - 2, point[1] + 2, point[2] + 2, outline="black")
        canvas.tag_bind(oval, "<Button-1>", lambda event, p=point: display_point_info(event, p))

    print("Total points in range : ",len(data_points))

    for row in data_points:
        new_point = Point(row[1], row[2])  # Create a Point instance from the retrieved tuple
        qtree.insert(new_point)

    # Draw the QuadTree nodes on the canvas
    qtree.draw(canvas)
    qtree.delete_from_canvas(canvas)

    prev_x, prev_y = None, None


def print_quadtree_tags():
    if quadtree_object_id:
        canvas.delete(quadtree_object_id)
    else:
        print("No QuadTree object found to delete.")

def on_mouse_motion(event):
    # Move the rectangle based on mouse movement when the button is pressed
    global prev_x, prev_y
    x, y = event.x, event.y
    if prev_x is not None and prev_y is not None:
        canvas.move(rectangle, x - prev_x, y - prev_y)
        prev_x, prev_y = x, y

def zoom(event):
    global zoom_scale
    zoom_factor = 1.1 if event.delta > 0 else 0.9  # Set zoom in/out factor

    # Get the current rectangle coordinates
    rect_coords = canvas.coords(rectangle)
    rect_center_x = (rect_coords[0] + rect_coords[2]) / 2
    rect_center_y = (rect_coords[1] + rect_coords[3]) / 2

    new_width = (rect_coords[2] - rect_coords[0]) * zoom_factor
    new_height = (rect_coords[3] - rect_coords[1]) * zoom_factor

    # Calculate new coordinates for the rectangle keeping the center constant
    new_x1 = rect_center_x - new_width / 2
    new_y1 = rect_center_y - new_height / 2
    new_x2 = rect_center_x + new_width / 2
    new_y2 = rect_center_y + new_height / 2

    # Limit zoom-out to original canvas size
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    if new_width < canvas_width and new_height < canvas_height:
        canvas.coords(rectangle, new_x1, new_y1, new_x2, new_y2)
        canvas.scale("rectangle", event.x, event.y, zoom_factor, zoom_factor)

    # Display updated coordinates after zoom
    print("Current position after zoom:")
    print(f"Top-Left: ({new_x1}, {new_y1})")
    print(f"Bottom-Right: ({new_x2}, {new_y2})")


def close_connection():
    cursor.close()
    conn.close()

# Create the main window.
root = tk.Tk()
root.title("Tkinter Rectangle Example")
root.protocol("WM_DELETE_WINDOW", close_connection)  # Close connection when closing the window

# Create a canvas to draw on.
canvas = tk.Canvas(root, width=900, height=650)
canvas.pack()

# Draw a rectangle on the canvas.
rectangle_area = canvas.create_rectangle(50, 50, 850, 600, outline="black", fill="#d8e1f0")

# Create an interactive rectangle on the canvas
rectangle = canvas.create_rectangle(50, 50, 200, 200, fill="grey")

quad_drawer = QuadTreeDrawer(canvas, None, None)


# Function to display point information and change the color of the clicked point
def display_point_info(event, point):
    global clicked_point

    if clicked_point:
        # Change the color of the previous clicked point back to grey.
        canvas.itemconfig(clicked_point, outline="black")

    # Set the clicked point to the current point.
    clicked_point = event.widget.find_closest(event.x, event.y)

    # Change the color of the clicked point to red.
    canvas.itemconfig(clicked_point, outline="red")

    # Display the point information.
    print("Point Selection:")
    print("ID:", point[0])
    print("X:", point[1])
    print("Y:", point[2])

# Bind mouse interaction functions
canvas.bind("<ButtonPress-1>", on_button_press)
canvas.bind("<ButtonRelease-1>", on_button_release)
canvas.bind("<B1-Motion>", on_mouse_motion)
canvas.bind("<MouseWheel>", zoom)

# Start the Tkinter main loop.
root.mainloop()

print_quadtree_tags()
