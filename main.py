import flet as ft


def main(page: ft.Page):
    headline = ft.Row(controls=[ft.Text(text_align=ft.TextAlign.CENTER, value=f"abaton measurement box", size=60,weight=ft.FontWeight.W_100,)],
                      alignment=ft.MainAxisAlignment.CENTER)
    page.controls.append(headline)


    # Create a text element to display messages
    message = ft.Text("")

    # Define button click handlers
    def calibrate_click(e):
        message.value = "calibrating ..."
        page.update()

    def test_click(e):
        message.value = "testing..."
        page.update()

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
