import dearpygui.dearpygui as dpg

dpg.create_context()

def change_text():
    print("Clicked!")

with dpg.window(label="Board"):
    with dpg.drawlist(width=200, height=200, tag="drawlist"):
        dpg.draw_circle([100, 100], 100, fill=[255, 255, 255, 100], tag="Circle_id")
    
    with dpg.item_handler_registry(tag="widget handler"):
        dpg.add_item_clicked_handler(callback=change_text)

    dpg.bind_item_handler_registry("drawlist", "widget handler")

with dpg.window(label="Cards"):
    dpg.add_text("Hand of cards")

with dpg.window(label="info"):
    dpg.add_text("info stuff and interaction buttons")
    

dpg.create_viewport(title='Custom Title', width=600, height=200)
dpg.setup_dearpygui()
dpg.show_viewport()

# below replaces, start_dearpygui()
while dpg.is_dearpygui_running():
    # insert here any code you would like to run in the render loop
    # you can manually stop by using stop_dearpygui()
    #print("this will run every frame")
    dpg.render_dearpygui_frame()

dpg.destroy_context()