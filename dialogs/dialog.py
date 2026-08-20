from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select, Row, Column, RequestContact
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory
from aiogram.enums import ContentType

from dialogs import getters, states
from dialogs import callbacks
from services import dialog_widgets
from services.layouts import LAYOUTS


start_dialog = Dialog(
    Window(Format('{start_bot}'),
            DynamicMedia('photo'),
            Button(Format('{button_start}'), id='button_start', on_click=callbacks.select_collection),
        getter=getters.start_hi,
        state=states.StartSG.start)
    )


select_collection = Dialog(
    Window(
        Format('{collection_select}'),
        DynamicMedia('photo'),
        ScrollingGroup(
            Select(
                Format('{item[name]}'),
                id='collect',
                item_id_getter=lambda item: item['id'],
                items='materials',
                on_click=callbacks.material_selected # type: ignore
            ),
            id='material_scroll',
            width=1,
            height=7,
            hide_on_single_page=True
        ),
        Row(
            Button(Const('←'), id='group_prev', on_click=callbacks.group_prev),
            Button(Const('→'), id='group_next', on_click=callbacks.group_next)
        ),
        state=states.Select_collection_SG.select_material,
        getter=getters.material_selection),
    Window(
        DynamicMedia('photo'),
        Format('{choice_color}'),
        ScrollingGroup(
            Select(
                Format('{item[name]}'),
                id='choice_color',
                item_id_getter=lambda item: item['id'],
                items='name_color',
                on_click=callbacks.color_selected # type: ignore
            ),
            id='select_color',
            width=2,
            height=9,
            hide_on_single_page=True
        ),
        Button(Format('{choice_color_back}'), id='back_to_choice_material', on_click=callbacks.back_to_material_color),
        state=states.Select_collection_SG.select_view_color,
        getter=getters.select_color_gett),
    Window(
        DynamicMedia('photo'),
        Column(
            Button(Format('{choice_color_itog}'), id='choice_color_itog', on_click=callbacks.color_itog),
            Button(Format('{choice_color_back}'), id='choice_color_back', on_click=callbacks.back_to_choice_color)
            ),
        state=states.Select_collection_SG.select_color_with_photo,
        getter=getters.select_photo_by_color_id
    ),
    Window(
        Format('{choice_size_tile}'),
        Column(
            Button(Format('{size_big}'), id='size_big', on_click=callbacks.save_size_layout),
            Button(Format('{size_average}'), id='size_average', on_click=callbacks.save_size_layout),
            Button(Format('{size_small}'), id='size_small', on_click=callbacks.save_size_layout)
        ),
        state=states.Select_collection_SG.select_size_tile,
        getter=getters.size_tile_gett
    ),
    Window(
        DynamicMedia('photo'),
        Format('{choice_layout_tile}'),
        Column(
            Button(Const(LAYOUTS['horizontal_straight']['label']), id='horizontal_straight', on_click=callbacks.save_type_layout_itog),
            Button(Const(LAYOUTS['horizontal_staggered']['label']), id='horizontal_staggered', on_click=callbacks.save_type_layout_itog),
            Button(Const(LAYOUTS['vertical_straight']['label']), id='vertical_straight', on_click=callbacks.save_type_layout_itog),
            Button(Const(LAYOUTS['vertical_staggered']['label']), id='vertical_staggered', on_click=callbacks.save_type_layout_itog)
        ),
        state=states.Select_collection_SG.select_layout_tile,
        getter=getters.layout_tile_gett
    ),
)


get_photo_user = Dialog(
    Window(
        Format('{waiting_photo}'),
        MessageInput(
            func=dialog_widgets.save_photo,
            content_types=ContentType.PHOTO
        ),
        state=states.Photo_visualization.get_user_photo,
        getter=getters.photo_reception
    ),

    Window(
        Format('{process_visual}'),
        state=states.Photo_visualization.processing_visualization,
        getter=getters.photo_in_process
    ),
)


forming_cards = Dialog(
    Window(
        Format('{ask_phone}'),
        RequestContact(Format('{share_phone}')),
        MessageInput(
            func=callbacks.phone_received,
            content_types=ContentType.CONTACT

        ),
        state=states.Forming_cards.get_user_phone,
        getter=getters.user_phone,
        markup_factory=ReplyKeyboardFactory(resize_keyboard=True)
    )
)