"""美剧口语训练：剧/集/场景/对白/表达卡/精学会话。"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.models import (
    AppUser,
    TvDialogueLine,
    TvEpisode,
    TvExpression,
    TvScene,
    TvShow,
    TvStudySession,
    UserSpeakingSentence,
    gen_id,
)
from app.schemas import (
    TvDialogueLineIn,
    TvDialogueLineOut,
    TvEpisodeCreate,
    TvEpisodeOut,
    TvEpisodeUpdate,
    TvExpressionCreate,
    TvExpressionOut,
    TvExpressionUpdate,
    TvHubOut,
    TvSceneCreate,
    TvSceneDetailOut,
    TvSceneOut,
    TvSceneUpdate,
    TvShowCreate,
    TvShowOut,
    TvShowUpdate,
    TvStudySessionOut,
    TvStudySessionUpdate,
    TvWeeklyReviewOut,
)
from app.services.srs import (
    is_due,
    now_naive,
    schedule_after_fail,
    schedule_after_success,
    schedule_first,
)
from app.timezone import now, today as today_str


def _ep_label(season: int, episode: int, title: str = "") -> str:
    base = f"S{int(season):02d}E{int(episode):02d}"
    return f"{base} {title}".strip() if title else base


def _session_out(s: TvStudySession) -> TvStudySessionOut:
    done = sum(
        [
            bool(s.step_blind),
            bool(s.step_parse),
            bool(s.step_shadow),
            bool(s.step_retell),
            bool(s.step_review),
        ]
    )
    return TvStudySessionOut(
        id=s.id,
        sceneId=s.scene_id,
        episodeId=s.episode_id or "",
        studyDate=s.study_date,
        stepBlind=bool(s.step_blind),
        stepParse=bool(s.step_parse),
        stepShadow=bool(s.step_shadow),
        stepRetell=bool(s.step_retell),
        stepReview=bool(s.step_review),
        blindNote=s.blind_note or "",
        retellText=s.retell_text or "",
        retellSeconds=int(s.retell_seconds or 0),
        durationSec=int(s.duration_sec or 0),
        completedCount=done,
        createdAt=s.created_at,
        updatedAt=s.updated_at,
    )


def _line_out(l: TvDialogueLine) -> TvDialogueLineOut:
    return TvDialogueLineOut(
        id=l.id,
        sceneId=l.scene_id,
        speaker=l.speaker or "",
        en=l.en or "",
        zh=l.zh or "",
        phoneticNote=l.phonetic_note or "",
        sortOrder=int(l.sort_order or 0),
    )


def _expr_out(e: TvExpression) -> TvExpressionOut:
    return TvExpressionOut(
        id=e.id,
        sceneId=e.scene_id,
        episodeId=e.episode_id,
        showId=e.show_id,
        phrase=e.phrase or "",
        meaning=e.meaning or "",
        usageScene=e.usage_scene or "",
        similar=e.similar or "",
        myExample=e.my_example or "",
        lifeUse=e.life_use or "",
        sourceLine=e.source_line or "",
        reviewStage=int(e.review_stage or 0),
        nextReviewAt=e.next_review_at,
        reviewCount=int(e.review_count or 0),
        mastered=bool(e.mastered),
        due=(not bool(e.mastered)) and is_due(e.next_review_at),
        createdAt=e.created_at,
        updatedAt=e.updated_at,
    )


def _scene_counts(db: Session, scene_id: str) -> tuple[int, int]:
    lc = db.query(TvDialogueLine).filter(TvDialogueLine.scene_id == scene_id).count()
    ec = db.query(TvExpression).filter(TvExpression.scene_id == scene_id).count()
    return lc, ec


def _get_today_session(db: Session, user_id: str, scene_id: str) -> TvStudySession | None:
    return (
        db.query(TvStudySession)
        .filter(
            TvStudySession.user_id == user_id,
            TvStudySession.scene_id == scene_id,
            TvStudySession.study_date == today_str(),
        )
        .first()
    )


def _scene_out(db: Session, user: AppUser, s: TvScene) -> TvSceneOut:
    lc, ec = _scene_counts(db, s.id)
    sess = _get_today_session(db, user.id, s.id)
    return TvSceneOut(
        id=s.id,
        episodeId=s.episode_id,
        title=s.title or "",
        timeRange=s.time_range or "",
        sceneSummary=s.scene_summary or "",
        targetCount=int(s.target_count or 3),
        sortOrder=int(s.sort_order or 0),
        lineCount=lc,
        expressionCount=ec,
        todaySession=_session_out(sess) if sess else None,
        createdAt=s.created_at,
        updatedAt=s.updated_at,
    )


def count_due_expressions(db: Session, user_id: str) -> int:
    ts = now_naive()
    return (
        db.query(TvExpression)
        .filter(
            TvExpression.user_id == user_id,
            TvExpression.mastered.is_(False),
            (TvExpression.next_review_at.is_(None)) | (TvExpression.next_review_at <= ts),
        )
        .count()
    )


# ----- Shows -----


def list_shows(db: Session, user: AppUser) -> list[TvShowOut]:
    rows = (
        db.query(TvShow)
        .filter(TvShow.user_id == user.id)
        .order_by(TvShow.sort_order.desc(), TvShow.updated_at.desc())
        .all()
    )
    out: list[TvShowOut] = []
    for r in rows:
        ep_c = db.query(TvEpisode).filter(TvEpisode.show_id == r.id).count()
        ex_c = db.query(TvExpression).filter(TvExpression.show_id == r.id).count()
        out.append(
            TvShowOut(
                id=r.id,
                title=r.title,
                stage=r.stage or "beginner",
                reason=r.reason or "",
                note=r.note or "",
                coverUrl=r.cover_url or "",
                sortOrder=int(r.sort_order or 0),
                episodeCount=ep_c,
                expressionCount=ex_c,
                createdAt=r.created_at,
                updatedAt=r.updated_at,
            )
        )
    return out


def create_show(db: Session, user: AppUser, body: TvShowCreate) -> TvShowOut:
    title = (body.title or "").strip()
    if not title:
        raise ValueError("请填写剧名")
    m = TvShow(
        id=gen_id("tvs"),
        user_id=user.id,
        title=title,
        stage=(body.stage or "beginner").strip(),
        reason=(body.reason or "").strip(),
        note=(body.note or "").strip(),
        cover_url=(body.coverUrl or "").strip(),
        sort_order=int(body.sortOrder or 0),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return TvShowOut(
        id=m.id,
        title=m.title,
        stage=m.stage,
        reason=m.reason or "",
        note=m.note or "",
        coverUrl=m.cover_url or "",
        sortOrder=m.sort_order or 0,
        episodeCount=0,
        expressionCount=0,
        createdAt=m.created_at,
        updatedAt=m.updated_at,
    )


def update_show(db: Session, user: AppUser, show_id: str, body: TvShowUpdate) -> TvShowOut | None:
    m = db.query(TvShow).filter(TvShow.id == show_id, TvShow.user_id == user.id).first()
    if not m:
        return None
    data = body.model_dump(exclude_unset=True)
    mapping = {"coverUrl": "cover_url", "sortOrder": "sort_order"}
    for k, v in data.items():
        setattr(m, mapping.get(k, k), v.strip() if isinstance(v, str) else v)
    if not (m.title or "").strip():
        raise ValueError("剧名不能为空")
    db.commit()
    db.refresh(m)
    return next((x for x in list_shows(db, user) if x.id == m.id), None)


def delete_show(db: Session, user: AppUser, show_id: str) -> bool:
    m = db.query(TvShow).filter(TvShow.id == show_id, TvShow.user_id == user.id).first()
    if not m:
        return False
    eps = db.query(TvEpisode).filter(TvEpisode.show_id == show_id).all()
    for ep in eps:
        _delete_episode_cascade(db, user, ep)
    db.delete(m)
    db.commit()
    return True


def _delete_episode_cascade(db: Session, user: AppUser, ep: TvEpisode) -> None:
    scenes = db.query(TvScene).filter(TvScene.episode_id == ep.id).all()
    for sc in scenes:
        _delete_scene_cascade(db, sc)
    db.query(TvExpression).filter(TvExpression.episode_id == ep.id).delete()
    db.delete(ep)


def _delete_scene_cascade(db: Session, sc: TvScene) -> None:
    db.query(TvDialogueLine).filter(TvDialogueLine.scene_id == sc.id).delete()
    db.query(TvStudySession).filter(TvStudySession.scene_id == sc.id).delete()
    db.query(TvExpression).filter(TvExpression.scene_id == sc.id).delete()
    db.delete(sc)


# ----- Episodes -----


def list_episodes(db: Session, user: AppUser, show_id: str) -> list[TvEpisodeOut]:
    rows = (
        db.query(TvEpisode)
        .filter(TvEpisode.user_id == user.id, TvEpisode.show_id == show_id)
        .order_by(TvEpisode.season.asc(), TvEpisode.episode.asc())
        .all()
    )
    out: list[TvEpisodeOut] = []
    for r in rows:
        sc = db.query(TvScene).filter(TvScene.episode_id == r.id).count()
        ex = db.query(TvExpression).filter(TvExpression.episode_id == r.id).count()
        out.append(
            TvEpisodeOut(
                id=r.id,
                showId=r.show_id,
                season=int(r.season or 1),
                episode=int(r.episode or 1),
                title=r.title or "",
                summary=r.summary or "",
                status=r.status or "todo",
                sceneCount=sc,
                expressionCount=ex,
                label=_ep_label(r.season or 1, r.episode or 1, r.title or ""),
                createdAt=r.created_at,
                updatedAt=r.updated_at,
            )
        )
    return out


def create_episode(db: Session, user: AppUser, body: TvEpisodeCreate) -> TvEpisodeOut:
    show = db.query(TvShow).filter(TvShow.id == body.showId, TvShow.user_id == user.id).first()
    if not show:
        raise ValueError("剧目不存在")
    m = TvEpisode(
        id=gen_id("tve"),
        user_id=user.id,
        show_id=body.showId,
        season=int(body.season or 1),
        episode=int(body.episode or 1),
        title=(body.title or "").strip(),
        summary=(body.summary or "").strip(),
        status=(body.status or "todo").strip(),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return TvEpisodeOut(
        id=m.id,
        showId=m.show_id,
        season=int(m.season or 1),
        episode=int(m.episode or 1),
        title=m.title or "",
        summary=m.summary or "",
        status=m.status or "todo",
        sceneCount=0,
        expressionCount=0,
        label=_ep_label(m.season or 1, m.episode or 1, m.title or ""),
        createdAt=m.created_at,
        updatedAt=m.updated_at,
    )


def update_episode(
    db: Session, user: AppUser, episode_id: str, body: TvEpisodeUpdate
) -> TvEpisodeOut | None:
    m = db.query(TvEpisode).filter(TvEpisode.id == episode_id, TvEpisode.user_id == user.id).first()
    if not m:
        return None
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(m, k, v.strip() if isinstance(v, str) else v)
    db.commit()
    items = list_episodes(db, user, m.show_id)
    return next((x for x in items if x.id == m.id), None)


def delete_episode(db: Session, user: AppUser, episode_id: str) -> bool:
    m = db.query(TvEpisode).filter(TvEpisode.id == episode_id, TvEpisode.user_id == user.id).first()
    if not m:
        return False
    _delete_episode_cascade(db, user, m)
    db.commit()
    return True


# ----- Scenes -----


def list_scenes(db: Session, user: AppUser, episode_id: str) -> list[TvSceneOut]:
    rows = (
        db.query(TvScene)
        .filter(TvScene.user_id == user.id, TvScene.episode_id == episode_id)
        .order_by(TvScene.sort_order.asc(), TvScene.created_at.asc())
        .all()
    )
    return [_scene_out(db, user, r) for r in rows]


def _replace_lines(db: Session, user: AppUser, scene_id: str, lines: list[TvDialogueLineIn]) -> None:
    db.query(TvDialogueLine).filter(TvDialogueLine.scene_id == scene_id).delete()
    for i, ln in enumerate(lines or []):
        if not (ln.en or "").strip() and not (ln.zh or "").strip():
            continue
        db.add(
            TvDialogueLine(
                id=gen_id("tvdl"),
                user_id=user.id,
                scene_id=scene_id,
                speaker=(ln.speaker or "").strip(),
                en=(ln.en or "").strip(),
                zh=(ln.zh or "").strip(),
                phonetic_note=(ln.phoneticNote or "").strip(),
                sort_order=int(ln.sortOrder if ln.sortOrder is not None else i),
            )
        )


def create_scene(db: Session, user: AppUser, body: TvSceneCreate) -> TvSceneDetailOut:
    ep = db.query(TvEpisode).filter(TvEpisode.id == body.episodeId, TvEpisode.user_id == user.id).first()
    if not ep:
        raise ValueError("剧集不存在")
    m = TvScene(
        id=gen_id("tvsc"),
        user_id=user.id,
        episode_id=body.episodeId,
        title=(body.title or "").strip() or "精学片段",
        time_range=(body.timeRange or "").strip(),
        scene_summary=(body.sceneSummary or "").strip(),
        target_count=int(body.targetCount or 3),
        sort_order=int(body.sortOrder or 0),
    )
    db.add(m)
    db.flush()
    _replace_lines(db, user, m.id, body.lines or [])
    if ep.status == "todo":
        ep.status = "learning"
    db.commit()
    db.refresh(m)
    return get_scene(db, user, m.id)  # type: ignore


def update_scene(
    db: Session, user: AppUser, scene_id: str, body: TvSceneUpdate
) -> TvSceneDetailOut | None:
    m = db.query(TvScene).filter(TvScene.id == scene_id, TvScene.user_id == user.id).first()
    if not m:
        return None
    data = body.model_dump(exclude_unset=True)
    lines = data.pop("lines", None)
    mapping = {
        "timeRange": "time_range",
        "sceneSummary": "scene_summary",
        "targetCount": "target_count",
        "sortOrder": "sort_order",
    }
    for k, v in data.items():
        setattr(m, mapping.get(k, k), v.strip() if isinstance(v, str) else v)
    if lines is not None:
        parsed = [
            x if isinstance(x, TvDialogueLineIn) else TvDialogueLineIn(**x) for x in lines
        ]
        _replace_lines(db, user, m.id, parsed)
    db.commit()
    return get_scene(db, user, m.id)


def get_scene(db: Session, user: AppUser, scene_id: str) -> TvSceneDetailOut | None:
    m = db.query(TvScene).filter(TvScene.id == scene_id, TvScene.user_id == user.id).first()
    if not m:
        return None
    base = _scene_out(db, user, m)
    lines = (
        db.query(TvDialogueLine)
        .filter(TvDialogueLine.scene_id == scene_id)
        .order_by(TvDialogueLine.sort_order.asc())
        .all()
    )
    exprs = (
        db.query(TvExpression)
        .filter(TvExpression.scene_id == scene_id, TvExpression.user_id == user.id)
        .order_by(TvExpression.created_at.desc())
        .all()
    )
    return TvSceneDetailOut(
        **base.model_dump(),
        lines=[_line_out(x) for x in lines],
        expressions=[_expr_out(x) for x in exprs],
    )


def delete_scene(db: Session, user: AppUser, scene_id: str) -> bool:
    m = db.query(TvScene).filter(TvScene.id == scene_id, TvScene.user_id == user.id).first()
    if not m:
        return False
    _delete_scene_cascade(db, m)
    db.commit()
    return True


# ----- Expressions -----


def list_expressions(
    db: Session,
    user: AppUser,
    *,
    status: str | None = None,
    scene_id: str | None = None,
) -> list[TvExpressionOut]:
    q = db.query(TvExpression).filter(TvExpression.user_id == user.id)
    if scene_id:
        q = q.filter(TvExpression.scene_id == scene_id)
    rows = q.order_by(TvExpression.updated_at.desc()).all()
    outs = [_expr_out(r) for r in rows]
    if status == "review":
        outs = [o for o in outs if o.due and not o.mastered]
    elif status == "mastered":
        outs = [o for o in outs if o.mastered]
    elif status == "learning":
        outs = [o for o in outs if not o.mastered]
    return outs


def create_expression(db: Session, user: AppUser, body: TvExpressionCreate) -> TvExpressionOut:
    phrase = (body.phrase or "").strip()
    if not phrase:
        raise ValueError("请填写句型")
    show_id = body.showId
    episode_id = body.episodeId
    if body.sceneId:
        sc = db.query(TvScene).filter(TvScene.id == body.sceneId, TvScene.user_id == user.id).first()
        if sc:
            episode_id = episode_id or sc.episode_id
            ep = db.query(TvEpisode).filter(TvEpisode.id == sc.episode_id).first()
            if ep:
                show_id = show_id or ep.show_id
    stage, next_at = schedule_first()
    m = TvExpression(
        id=gen_id("tvex"),
        user_id=user.id,
        scene_id=body.sceneId,
        episode_id=episode_id,
        show_id=show_id,
        phrase=phrase,
        meaning=(body.meaning or "").strip(),
        usage_scene=(body.usageScene or "").strip(),
        similar=(body.similar or "").strip(),
        my_example=(body.myExample or "").strip(),
        life_use=(body.lifeUse or "").strip(),
        source_line=(body.sourceLine or "").strip(),
        review_stage=stage,
        next_review_at=next_at,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _expr_out(m)


def update_expression(
    db: Session, user: AppUser, expr_id: str, body: TvExpressionUpdate
) -> TvExpressionOut | None:
    m = db.query(TvExpression).filter(TvExpression.id == expr_id, TvExpression.user_id == user.id).first()
    if not m:
        return None
    data = body.model_dump(exclude_unset=True)
    mapping = {
        "usageScene": "usage_scene",
        "myExample": "my_example",
        "lifeUse": "life_use",
        "sourceLine": "source_line",
    }
    for k, v in data.items():
        setattr(m, mapping.get(k, k), v.strip() if isinstance(v, str) else v)
    if not (m.phrase or "").strip():
        raise ValueError("句型不能为空")
    db.commit()
    db.refresh(m)
    return _expr_out(m)


def delete_expression(db: Session, user: AppUser, expr_id: str) -> bool:
    m = db.query(TvExpression).filter(TvExpression.id == expr_id, TvExpression.user_id == user.id).first()
    if not m:
        return False
    db.delete(m)
    db.commit()
    return True


def review_expression(db: Session, user: AppUser, expr_id: str, result: str = "good") -> TvExpressionOut | None:
    m = db.query(TvExpression).filter(TvExpression.id == expr_id, TvExpression.user_id == user.id).first()
    if not m:
        return None
    m.review_count = int(m.review_count or 0) + 1
    if result == "again":
        stage, next_at = schedule_after_fail()
        m.review_stage = stage
        m.next_review_at = next_at
        m.mastered = False
    else:
        stage, next_at, mastered = schedule_after_success(int(m.review_stage or 0))
        m.review_stage = stage
        m.next_review_at = next_at
        m.mastered = mastered
    db.commit()
    db.refresh(m)
    return _expr_out(m)


# ----- Study session -----


def get_or_create_session(db: Session, user: AppUser, scene_id: str) -> TvStudySessionOut:
    sc = db.query(TvScene).filter(TvScene.id == scene_id, TvScene.user_id == user.id).first()
    if not sc:
        raise ValueError("场景不存在")
    s = _get_today_session(db, user.id, scene_id)
    if not s:
        s = TvStudySession(
            id=gen_id("tvss"),
            user_id=user.id,
            scene_id=scene_id,
            episode_id=sc.episode_id,
            study_date=today_str(),
        )
        db.add(s)
        db.commit()
        db.refresh(s)
    return _session_out(s)


def update_session(
    db: Session, user: AppUser, scene_id: str, body: TvStudySessionUpdate
) -> TvStudySessionOut:
    get_or_create_session(db, user, scene_id)
    s = _get_today_session(db, user.id, scene_id)
    assert s
    data = body.model_dump(exclude_unset=True)
    mapping = {
        "stepBlind": "step_blind",
        "stepParse": "step_parse",
        "stepShadow": "step_shadow",
        "stepRetell": "step_retell",
        "stepReview": "step_review",
        "blindNote": "blind_note",
        "retellText": "retell_text",
        "retellSeconds": "retell_seconds",
        "durationSec": "duration_sec",
    }
    for k, v in data.items():
        setattr(s, mapping.get(k, k), v)
    # 五步都完成时，标记剧集 done（若该集所有场景今日都完成则可后续扩展；这里先标 learning）
    ep = db.query(TvEpisode).filter(TvEpisode.id == s.episode_id).first()
    if ep and ep.status == "todo":
        ep.status = "learning"
    completed = all(
        [s.step_blind, s.step_parse, s.step_shadow, s.step_retell, s.step_review]
    )
    if completed and ep:
        # 若该集所有场景都有完成过的会话，标 done
        scenes = db.query(TvScene).filter(TvScene.episode_id == ep.id).all()
        all_done = True
        for sc in scenes:
            any_done = (
                db.query(TvStudySession)
                .filter(
                    TvStudySession.scene_id == sc.id,
                    TvStudySession.step_review.is_(True),
                )
                .first()
            )
            if not any_done:
                all_done = False
                break
        if all_done and scenes:
            ep.status = "done"
    db.commit()
    db.refresh(s)
    return _session_out(s)


# ----- Hub / weekly -----


def get_hub(db: Session, user: AppUser) -> TvHubOut:
    shows = db.query(TvShow).filter(TvShow.user_id == user.id).count()
    total = db.query(TvExpression).filter(TvExpression.user_id == user.id).count()
    mastered = (
        db.query(TvExpression)
        .filter(TvExpression.user_id == user.id, TvExpression.mastered.is_(True))
        .count()
    )
    due = count_due_expressions(db, user.id)
    # 进行中的场景：今日有会话但未完成五步，或最近更新的场景
    today = today_str()
    sessions = (
        db.query(TvStudySession)
        .filter(TvStudySession.user_id == user.id, TvStudySession.study_date == today)
        .order_by(TvStudySession.updated_at.desc())
        .limit(8)
        .all()
    )
    active: list[TvSceneOut] = []
    for sess in sessions:
        sc = db.query(TvScene).filter(TvScene.id == sess.scene_id).first()
        if sc:
            active.append(_scene_out(db, user, sc))
    return TvHubOut(
        showCount=shows,
        expressionDueCount=due,
        expressionTotal=total,
        expressionMastered=mastered,
        activeScenes=active,
    )


def get_weekly_review(db: Session, user: AppUser) -> TvWeeklyReviewOut:
    end = now().date()
    start = end - timedelta(days=6)
    start_s = start.isoformat()
    end_s = end.isoformat()
    sessions = (
        db.query(TvStudySession)
        .filter(
            TvStudySession.user_id == user.id,
            TvStudySession.study_date >= start_s,
            TvStudySession.study_date <= end_s,
        )
        .all()
    )
    completed = [s for s in sessions if s.step_review]
    new_expr = (
        db.query(TvExpression)
        .filter(
            TvExpression.user_id == user.id,
            TvExpression.created_at >= now_naive() - timedelta(days=7),
        )
        .count()
    )
    mastered = (
        db.query(TvExpression)
        .filter(
            TvExpression.user_id == user.id,
            TvExpression.mastered.is_(True),
            TvExpression.updated_at >= now_naive() - timedelta(days=7),
        )
        .count()
    )
    # 跟读：美剧场景写入的 note=tvsc:… 或标题含 · TV
    from sqlalchemy import or_

    shadow = (
        db.query(UserSpeakingSentence)
        .filter(
            UserSpeakingSentence.user_id == user.id,
            UserSpeakingSentence.updated_at >= now_naive() - timedelta(days=7),
            or_(
                UserSpeakingSentence.note.like("tvsc:%"),
                UserSpeakingSentence.article_title.like("%· TV%"),
            ),
        )
        .count()
    )
    eps = {s.episode_id for s in sessions if s.episode_id}
    duration = sum(int(s.duration_sec or 0) for s in sessions)
    return TvWeeklyReviewOut(
        weekStart=start_s,
        weekEnd=end_s,
        sessionCount=len(sessions),
        completedSessionCount=len(completed),
        newExpressionCount=new_expr,
        masteredCount=mastered,
        shadowCount=shadow,
        episodesTouched=len(eps),
        durationSec=duration,
    )
