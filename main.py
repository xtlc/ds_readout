import flet as ft

import sys
import io
import time

class PrintCapture(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, message):
        super().write(message)
        # Update the Flet text component with the new message
        self.text_widget.value += message
        self.text_widget.update()


class MyClass:
    def __init__(self):
        self.do_something()

    def do_something(self):
        print("Doing something...")
        time.sleep(2)
        print("Something is done!")

def main(page: ft.Page):
    headline = ft.Row(controls=[ft.Text(text_align=ft.TextAlign.CENTER, value=f"abaton measurement box", size=60,weight=ft.FontWeight.W_100,)],
                      alignment=ft.MainAxisAlignment.CENTER)
    page.controls.append(headline)


    # Create a text element to display messages
    message = ft.Text("")
    captured_text = PrintCapture(message)
    sys.stdout = captured_text

    # Define button click handlers
    def calibrate_click(e):
        message.value = "calibrating ..."
        print("yoour mux")
        from scales import Mux
        message.value="MUX imported"
        s = Mux(device="ttyUSB1", uid="0020240425142741", number_of_scales=2, max_values=0, sleep_time=0)
        s.zero_all_scales()
        page.update()

    def test_click(e):
        print ("aldaaaeeer!")
        #page.update()

    def log_click(e):
        message.value = "logging..."
        page.update()

    # Create buttons
    calibrate_button = ft.ElevatedButton("Calibrate", on_click=calibrate_click)
    test_button = ft.ElevatedButton("Test", on_click=test_click)
    log_button = ft.ElevatedButton("Log", on_click=log_click)

    # Create a row with buttons and set the alignment and spacing
    button_row = ft.Row(controls=[calibrate_button, test_button, log_button], alignment=ft.MainAxisAlignment.CENTER, spacing=20,)

    # Add the row and message to the page
    page.add(button_row, message)
    


ft.app(main)
