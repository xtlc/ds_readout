import flet as ft


def main(page: ft.Page):
    headline = "abaton measurement box"
    t = ft.Text(value=headline, color="green", size=36, text_align="center")
    page.controls.append(t)


    btn_calibrate_btn = ft.ElevatedButton("calibrate scales")
    btn_measure = ft.ElevatedButton("measure")
    btn_to_influx = ft.ElevatedButton("log")
    page.update()

ft.app(main)
