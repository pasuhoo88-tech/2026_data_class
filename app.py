import calendar
from datetime import date

import streamlit as st


def initialize_state() -> None:
    """세션에서 사용할 일정 목록과 현재 달을 준비합니다."""
    if "todos" not in st.session_state:
        st.session_state.todos = []
    if "next_todo_id" not in st.session_state:
        st.session_state.next_todo_id = 1
    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = date.today().replace(day=1)
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = date.today()

    # 날짜 기능을 추가하기 전 세션에 남아 있던 일정도 계속 사용할 수 있게 합니다.
    for todo in st.session_state.todos:
        todo.setdefault("date", date.today())


def add_todo(title: str, todo_date: date) -> None:
    """선택한 날짜에 새 미완료 일정을 추가합니다."""
    cleaned_title = title.strip()
    if cleaned_title:
        st.session_state.todos.append(
            {
                "id": st.session_state.next_todo_id,
                "title": cleaned_title,
                "date": todo_date,
                "completed": False,
            }
        )
        st.session_state.next_todo_id += 1


def delete_todo(todo_id: int) -> None:
    """식별자가 일치하는 일정을 삭제합니다."""
    st.session_state.todos = [
        todo for todo in st.session_state.todos if todo["id"] != todo_id
    ]


def update_todo_completion(todo_id: int, checkbox_key: str) -> None:
    """체크박스의 현재 값을 해당 일정에 저장합니다."""
    for todo in st.session_state.todos:
        if todo["id"] == todo_id:
            todo["completed"] = st.session_state[checkbox_key]
            break


def move_month(month_offset: int) -> None:
    """달력의 표시 월을 앞뒤로 이동합니다."""
    current_month = st.session_state.calendar_month
    month_index = current_month.month - 1 + month_offset
    year = current_month.year + month_index // 12
    month = month_index % 12 + 1
    st.session_state.calendar_month = date(year, month, 1)


def render_summary() -> None:
    """전체 완료 및 미완료 일정 개수를 표시합니다."""
    completed_count = sum(todo["completed"] for todo in st.session_state.todos)
    total_count = len(st.session_state.todos)
    summary_columns = st.columns(3)
    summary_columns[0].metric("전체", total_count)
    summary_columns[1].metric("미완료", total_count - completed_count)
    summary_columns[2].metric("완료", completed_count)


def render_calendar() -> None:
    """날짜를 직접 선택할 수 있는 월간 달력을 렌더링합니다."""
    current_month = st.session_state.calendar_month
    month_label = f"{current_month.year}년 {current_month.month}월"

    header_columns = st.columns([0.15, 0.7, 0.15])
    if header_columns[0].button("‹", key="previous_month", help="이전 달"):
        move_month(-1)
        st.rerun()
    header_columns[1].markdown(
        f"<h2 class='calendar-title'>{month_label}</h2>", unsafe_allow_html=True
    )
    if header_columns[2].button("›", key="next_month", help="다음 달"):
        move_month(1)
        st.rerun()

    month_calendar = calendar.Calendar(firstweekday=6).monthdatescalendar(
        current_month.year, current_month.month
    )
    weekday_names = ["일", "월", "화", "수", "목", "금", "토"]
    weekday_columns = st.columns(7)
    for column, weekday_name in zip(weekday_columns, weekday_names):
        column.markdown(f"<div class='weekday'>{weekday_name}</div>", unsafe_allow_html=True)

    todos_by_date = {}
    for todo in st.session_state.todos:
        if not todo["completed"]:
            todos_by_date.setdefault(todo["date"], []).append(todo)

    for week in month_calendar:
        day_columns = st.columns(7)
        for column, day in zip(day_columns, week):
            day_todos = todos_by_date.get(day, [])
            if column.button(
                    str(day.day),
                key=f"calendar_day_{day.isoformat()}",
                type="primary" if day == st.session_state.selected_date else "secondary",
                use_container_width=True,
            ):
                st.session_state.selected_date = day
                st.session_state.calendar_month = day.replace(day=1)
                st.session_state.date_picker = day
                st.rerun()
                column.markdown(
                    f"<div class='date-count'>{len(day_todos)}</div>",
                    unsafe_allow_html=True,
                )


def render_todo_list() -> None:
    """선택한 날짜의 일정과 완료 체크, 삭제 버튼을 표시합니다."""
    selected_date = st.session_state.selected_date
    selected_todos = [
        todo for todo in st.session_state.todos if todo["date"] == selected_date
    ]
    st.subheader(f"{selected_date.month}월 {selected_date.day}일 일정")

    if not selected_todos:
        st.info("선택한 날짜에 등록된 일정이 없습니다.")
        return

    for todo in selected_todos:
        todo_columns = st.columns([0.85, 0.15])
        checkbox_key = f"todo_{todo['id']}"
        todo_columns[0].checkbox(
            todo["title"],
            value=todo["completed"],
            key=checkbox_key,
            on_change=update_todo_completion,
            args=(todo["id"], checkbox_key),
        )
        if todo_columns[1].button("삭제", key=f"delete_{todo['id']}"):
            delete_todo(todo["id"])
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="일정 관리", page_icon="🗓️", layout="centered")
    st.markdown(
        """
        <style>
        .calendar-title { text-align: center; margin: 0.2rem 0 0.8rem; }
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, minmax(0, 1fr));
            gap: 6px;
            margin: 0.5rem 0 1.2rem;
        }
        .weekday {
            color: #64748b;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 0.35rem;
            text-align: center;
        }
        .date-count {
            color: #64748b;
            font-size: 0.7rem;
            line-height: 1;
            min-height: 0.8rem;
            padding: 0 0.35rem;
            text-align: right;
        }
        .day-cell {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            min-height: 52px;
            padding: 0.45rem;
            position: relative;
        }
        .day-cell.today { border: 2px solid #0f766e; }
        .day-cell.selected-day { background: #ccfbf1; border-color: #0f766e; }
        .day-cell.outside-month { color: #cbd5e1; background: #ffffff; }
        .todo-count {
            background: #0f766e;
            border-radius: 999px;
            color: white;
            font-size: 0.7rem;
            padding: 0.1rem 0.35rem;
            position: absolute;
            right: 0.4rem;
            bottom: 0.35rem;
        }
        @media (max-width: 600px) {
            .calendar-grid { gap: 3px; }
            .day-cell { min-height: 42px; padding: 0.3rem; font-size: 0.85rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    initialize_state()

    st.title("🗓️ 일정 관리")
    st.caption("날짜를 선택하고 해야 할 일을 기록해 보세요.")
    render_summary()
    render_calendar()

    selected_date = st.date_input(
        "일정을 추가하거나 확인할 날짜",
        value=st.session_state.selected_date,
        key="date_picker",
    )
    if selected_date != st.session_state.selected_date:
        st.session_state.selected_date = selected_date
        st.session_state.calendar_month = selected_date.replace(day=1)
        st.rerun()

    with st.form("add_todo_form", clear_on_submit=True):
        todo_title = st.text_input("새 일정", placeholder="예: 데이터 분석 보고서 작성")
        submitted = st.form_submit_button(
            "일정 추가", type="primary", use_container_width=True
        )
        if submitted:
            if todo_title.strip():
                add_todo(todo_title, st.session_state.selected_date)
                st.rerun()
            else:
                st.warning("일정 내용을 입력해 주세요.")

    st.divider()
    render_todo_list()


if __name__ == "__main__":
    main()
