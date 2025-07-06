from fastui import AnyComponent
from fastui import components as c
from fastui.events import GoToEvent

def base_page(
    *components: AnyComponent, title: str | None = None # , logged_in: bool = False
) -> list[AnyComponent]:
    portal_name = "Cytometry Manager"
    return [
        c.PageTitle(text=f"{portal_name} — {title}" if title else portal_name),
        c.Navbar(
            title=portal_name,
            title_event=GoToEvent(url="/"),
            start_links=[
                c.Link(
                    components=[c.Text(text="Projects")],
                    on_click=GoToEvent(url="/projects/"),
                    active="startswith:/projects/",
                ),
                c.Link(
                    components=[c.Text(text="Samples")],
                    on_click=GoToEvent(url="/samples/"),
                    active="startswith:/samples/",
                ),
                c.Link(
                    components=[c.Text(text="Subjects")],
                    on_click=GoToEvent(url="/subjects/"),
                    active="startswith:/subjects/",
                ),
                c.Link(
                    components=[c.Text(text="Cohorts")],
                    on_click=GoToEvent(url="/cohorts/"),
                    active="startswith:/cohorts/",
                ),
                c.Link(
                    components=[c.Text(text="Datasets")],
                    on_click=GoToEvent(url="/datasets/"),
                    active="startswith:/datasets/",
                ),
            ],
            end_links=[
                c.Link(
                    components=[c.Text(text="Help")],
                    on_click=GoToEvent(url="/help/"),
                    active="startswith:/help/",
                ),
            #    c.Link(
            #        components=[c.Text(text="Profile")],
            #        on_click=GoToEvent(url="/auth/profile"),
            #        active="startswith:/auth/profile",
            #    ),
            ]
            #if logged_in
            #else [
            #    c.Link(
            #        components=[c.Text(text="Login")],
            #        on_click=GoToEvent(url="/auth/login/password"),
            #    ),
            #    c.Link(
            #        components=[c.Text(text="Sign Up")],
            #        on_click=GoToEvent(url="/users/create"),
            #    )
            #],
        ),
        c.Page(
            components=[
                *((c.Heading(text=title),) if title else ()),
                *components,
            ],
        ),
        c.Footer(
            extra_text=portal_name,
            links=[],
        ),
    ]