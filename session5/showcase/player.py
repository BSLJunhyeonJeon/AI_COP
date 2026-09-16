"""player.py — 초파리 전뇌 시뮬레이션 재생기 (수업 시연용, Windows exe 로 빌드)

미리 계산된 pack/ 을 읽어 게임 화면 · flybody 3D 초파리 · 뇌 지도 · GF 막전위 · 전체 발화를 한 시간축으로 재생한다.
계산은 하지 않는다(make_pack.py 가 MODEL_SPEC §4 규칙으로 미리 해 둔 결과를 그대로 튼다).

조작:  1~5 속도 단계 선택   Space 재생/정지   ←/→ 한 프레임(2.5 ms)   Shift+←/→ 10 프레임
       [ / ] 배속 낮춤/높임   Home 처음부터   A 자동 재생(1→5 순서)   H 도움말   S 스크린샷   Esc 종료
CLI:   python player.py [--pack DIR] [--size 1600x900] [--screenshot K FRAME OUT.png]
"""
import argparse, json, math, os, sys, time
import numpy as np
import pygame

# ---------------- 경로 (PyInstaller onefile 대응) ----------------
def resource_dir():
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return base

# ---------------- 색 ----------------
BG = (14, 17, 22); PANEL = (20, 24, 31); GRID = (44, 50, 60); TEXT = (213, 219, 227); MUTED = (170, 180, 190); DIM = (127, 138, 150)
ORANGE = (255, 159, 26); RED = (255, 59, 48); TEAL = (26, 188, 156); BLUE = (46, 134, 193); LIGHT = (93, 173, 226); GREEN = (46, 204, 113)
GROUND = (61, 90, 61); CACTUS = (46, 204, 113); WHITE = (255, 255, 255)
SLOWMOS = [2, 4, 10, 20, 40]

class Pack:
    def __init__(self, d):
        self.dir = d
        self.meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
        self.arr = np.load(os.path.join(d, "episodes.npz"))
        self.frame_ms = float(self.meta["frame_ms"])
        self.brain_bg = pygame.image.load(os.path.join(d, "brain_bg.png"))
        self.fly3d = {k: [pygame.image.load(os.path.join(d, "fly3d", fn)) for fn in v] for k, v in self.meta["fly3d"].items()}
        self.fly2d = [pygame.image.load(os.path.join(d, f"fly2d_{i}.png")) for i in (0, 1)]   # convert 는 창이 생긴 뒤(Player)
    def ep(self, k):
        return self.meta["episodes"][str(k)]
    def a(self, k, name):
        return self.arr[f"k{k}_{name}"]

class Player:
    def __init__(self, pack, size=(1600, 900), headless=False):
        self.pack = pack; self.W, self.H = size
        flags = 0 if headless else pygame.RESIZABLE
        self.screen = pygame.display.set_mode(size, flags)
        pygame.display.set_caption("초파리 전뇌 시뮬레이션 재생기 — 공룡 게임")
        self.font = self._font(20); self.font_s = self._font(16); self.font_b = self._font(26, bold=True); self.font_xl = self._font(44, bold=True)
        self.k = 3; self.f = 0; self.playing = False; self.slow_i = 2; self.auto = False; self.help = True
        self.game_t = 0.0; self.last = time.time(); self.hold_until = None
        self.canvas = pygame.Surface(size)
        self.pack.fly2d = [im.convert_alpha() for im in self.pack.fly2d]
        self.pack.brain_bg = self.pack.brain_bg.convert()
        self.pack.fly3d = {k: [im.convert() for im in v] for k, v in self.pack.fly3d.items()}
        self._load_episode()
    def _font(self, size, bold=False):
        """팩에 든 나눔고딕(OFL)을 우선 쓴다 — 어느 PC 에서나 한글이 깨지지 않게. 없으면 시스템 한글 폰트."""
        fp = os.path.join(self.pack.dir, "NanumGothic.ttf")
        if os.path.isfile(fp):
            f = pygame.font.Font(fp, size); f.set_bold(bold); return f
        for cand in ("malgungothic,malgun gothic", "notosanscjkkr,notosanscjkjp", "applesdgothicneo"):
            try:
                f = pygame.font.SysFont(cand, size, bold=bold)
                if f: return f
            except Exception:
                pass
        return pygame.font.SysFont(None, size)
    def _load_episode(self):
        p = self.pack; k = self.k
        self.meta = p.ep(k); self.t = p.a(k, "t"); self.d = p.a(k, "d"); self.theta = p.a(k, "theta")
        self.now_x, self.now_y, self.now_c, self.now_off = p.a(k, "now_x"), p.a(k, "now_y"), p.a(k, "now_c"), p.a(k, "now_off")
        self.rec_x, self.rec_y, self.rec_off = p.a(k, "rec_x"), p.a(k, "rec_y"), p.a(k, "rec_off")
        self.vgf = p.a(k, "vgf"); self.pop = p.a(k, "pop"); self.n_f = len(self.t)
        self.f = min(self.f, self.n_f - 1); self.game_t = self.f * p.frame_ms
    # ---------------- 상태 ----------------
    def phase_at(self, t):
        m = self.meta; air = m["air"]; tgf = m["t_gf_first"]
        if tgf is not None and air is not None:
            if tgf <= t < air[0]: return "takeoff", (t - tgf) / (air[0] - tgf)
            if air[0] <= t <= air[1]: return "flight", (t - air[0]) / (air[1] - air[0])
            if air[1] < t <= air[1] + 40: return "landing", (t - air[1]) / 40.0
        if (not m["passed"]) and m["t_c"] <= t <= m["t_c"] + 60 and not (air and air[0] <= t <= air[1]):
            return "hit", 0.0
        return "rest", 0.0
    def state_text(self, t, th):
        m = self.meta; c = self.pack.meta["constants"]
        if m["t_on"] is None or t < m["t_on"]:
            return f"접근 중 — 각크기 θ = {th:4.1f}° (아직 {c['theta_on_deg']:.0f}° 미만, 뇌는 조용)", MUTED
        if m["t_gf_first"] is None or t < m["t_gf_first"]:
            return f"LOOMING — θ = {th:4.1f}° ≥ {c['theta_on_deg']:.0f}°, 시각 뉴런 LPLC2 210개 150 Hz 발화 중", ORANGE
        if t < m["air"][0]:
            return f"GF 스파이크! 자극 후 {m['t_gf_first']-m['t_on']:.1f} ms -> {c['t_motor_ms']:.0f} ms 뒤 점프", RED
        if t <= m["air"][1]:
            return f"점프 중 (공중 {c['T_jump_ms']:.0f} ms)", LIGHT
        return "착지", MUTED
    # ---------------- 그리기 ----------------
    def draw(self):
        S = self.canvas; S.fill(BG); W, H = self.W, self.H
        f = self.f; t = float(self.t[f]); d = float(self.d[f]); th = float(self.theta[f]); m = self.meta; c = self.pack.meta["constants"]
        # 헤더
        title = self.font_b.render("초파리 뇌(뉴런 138,639개)가 공룡 게임을 한다 — 재생기", True, WHITE); S.blit(title, (20, 14))
        sub = self.font.render(f"속도 단계 {self.k}/5 (v = {m['v']} 단위/ms)   ·   재생 1/{SLOWMOS[self.slow_i]} 배속   ·   t = {t:6.1f} ms   ·   {'> 재생 중' if self.playing else '|| 정지'}{'  · 자동' if self.auto else ''}", True, MUTED); S.blit(sub, (20, 48))
        # ---- 게임 패널 ----
        gx, gy, gw, gh = 20, 84, 970, 380
        pygame.draw.rect(S, PANEL, (gx, gy, gw, gh), border_radius=8)
        ground_y = gy + gh - 40; fly_x = gx + 110; scale = (gw - 150) / 104.0     # 단위 -14..90
        pygame.draw.rect(S, GROUND, (gx, ground_y, gw, 40), border_bottom_left_radius=8, border_bottom_right_radius=8)
        # 선인장
        if -3 < d < 94:
            cx = fly_x + d * scale; hpx = c["h"] * scale * 1.6
            pygame.draw.rect(S, CACTUS, (cx - 1.5 * scale, ground_y - hpx, 3 * scale, hpx))
            pygame.draw.rect(S, CACTUS, (cx - 3.5 * scale, ground_y - 0.7 * hpx, 2 * scale, 0.4 * hpx)); pygame.draw.rect(S, CACTUS, (cx + 1.5 * scale, ground_y - 0.6 * hpx, 2 * scale, 0.4 * hpx))
        # 초파리(2D)
        phase, u = self.phase_at(t)
        lift = 0.0
        if phase == "flight": lift = 22.0 * 4 * u * (1 - u) * scale * 1.6
        spr = self.pack.fly2d[(f // 2) % 2 if phase == "flight" else 0]
        spr = pygame.transform.smoothscale(spr, (int(14 * scale), int(14 * scale)))
        shake = int(6 * math.sin(f * 2.5)) if phase == "hit" else 0
        S.blit(spr, (fly_x - spr.get_width() // 2 + shake, ground_y - spr.get_height() * 0.92 - lift))
        # 상태 글
        S.blit(self.font_s.render(f"t = {t:6.1f} ms   선인장까지 {max(d,0):6.1f}   충돌 예정 {m['t_c']:.0f} ms", True, TEXT), (gx + 16, gy + 12))
        st, col = self.state_text(t, th); S.blit(self.font.render(st, True, col), (gx + 16, gy + 40))
        if t >= m["t_c"]:
            res = "통과" if m["passed"] else {"too_late": "충돌 — 너무 빨라서 늦음", "too_early": "충돌 — 너무 일찍 뛰어 착지", "no_jump": "충돌 — 점프 없음"}[m["reason"]]
            S.blit(self.font_xl.render(res, True, GREEN if m["passed"] else RED), (gx + 16, gy + 78))
        # ---- GF 막전위 ----
        self._plot_gf(S, 60, 500, 930, 190, t)
        # ---- 전체 발화 ----
        self._plot_pop(S, 60, 722, 930, 150, t)
        # ---- 뇌 지도 ----
        bx, by, bw, bh = 1010, 84, 570, 330
        pygame.draw.rect(S, PANEL, (bx, by, bw, bh), border_radius=8)
        bgw, bgh = self.pack.meta["brain_size"]; sc = min((bw - 10) / bgw, (bh - 30) / bgh)
        bg = pygame.transform.smoothscale(self.pack.brain_bg, (int(bgw * sc), int(bgh * sc))); ox = bx + (bw - bg.get_width()) // 2; oy = by + 24
        S.blit(bg, (ox, oy))
        S.blit(self.font_s.render("뇌 지도(정면) — 켜진 점 = 지금 발화 · 주황 LPLC2 · 빨간 별 GF · 청록 하류 · 파랑 직전 15 ms", True, MUTED), (bx + 10, by + 4))
        r0, r1 = self.rec_off[f], self.rec_off[f + 1]
        for x, y in zip(self.rec_x[r0:r1], self.rec_y[r0:r1]):
            if x >= 0: pygame.draw.circle(S, (35, 90, 140), (ox + int(x * sc), oy + int(y * sc)), 2)
        n0, n1 = self.now_off[f], self.now_off[f + 1]
        gf_pts = []
        for x, y, cl in zip(self.now_x[n0:n1], self.now_y[n0:n1], self.now_c[n0:n1]):
            if x < 0: continue
            p = (ox + int(x * sc), oy + int(y * sc))
            if cl == 2: gf_pts.append(p)
            else: pygame.draw.circle(S, ORANGE if cl == 1 else TEAL, p, 3)
        for p in gf_pts:
            pygame.draw.circle(S, WHITE, p, 11); pygame.draw.circle(S, RED, p, 9)
        # ---- 3D 초파리 ----
        px, py, ps = 1095, 430, 400
        pygame.draw.rect(S, (93, 109, 126), (px - 2, py - 2, ps + 4, ps + 4), border_radius=6)
        frames = self.pack.fly3d
        if phase == "takeoff": img = frames["takeoff"][min(int(u * len(frames["takeoff"])), len(frames["takeoff"]) - 1)]
        elif phase == "flight": img = frames["flight"][(f // 2) % len(frames["flight"])]
        elif phase == "landing": img = frames["landing"][min(int(u * len(frames["landing"])), len(frames["landing"]) - 1)]
        else: img = frames["rest"][0]
        lift3d = int(110 * 4 * u * (1 - u)) if phase == "flight" else 0
        clip = S.get_clip(); S.set_clip(pygame.Rect(px, py, ps, ps)); S.fill((0, 0, 0), (px, py, ps, ps))
        S.blit(img, (px + shake, py - lift3d)); S.set_clip(clip)
        lab = self.font_s.render("flybody 3D 초파리 (동기화)", True, WHITE); S.blit(lab, (px + ps // 2 - lab.get_width() // 2, py + ps - 26))
        # ---- 도움말 / 푸터 ----
        if self.help:
            S.blit(self.font_s.render("1~5 속도 단계 · Space 재생/정지 · 좌우 화살표 한 프레임(2.5 ms) · Shift+화살표 10프레임 · [ ] 배속 · Home 처음 · A 자동 재생 · H 도움말 · S 스크린샷 · Esc 종료", True, DIM), (20, H - 28))
        S.blit(self.font_s.render("FlyWire v783 (CC BY 4.0) · Shiu 2024 LIF · flybody (Apache-2.0) · 계산 결과 재생", True, DIM), (1010, H - 28))
        # 화면 크기가 다르면 맞춰 그린다
        if self.screen.get_size() != (W, H):
            self.screen.blit(pygame.transform.smoothscale(S, self.screen.get_size()), (0, 0))
        else:
            self.screen.blit(S, (0, 0))
    def _axes(self, S, x, y, w, h, title):
        pygame.draw.rect(S, PANEL, (x - 50, y - 26, w + 70, h + 60), border_radius=8)
        S.blit(self.font_s.render(title, True, TEXT), (x, y - 22))
        pygame.draw.rect(S, GRID, (x, y, w, h), 1)
    def _plot_gf(self, S, x, y, w, h, t):
        m = self.meta; T = m["T"]; c = self.pack.meta["constants"]; dt = m["dt_ms"]
        self._axes(S, x, y, w, h, "거대섬유 GF 막전위 (점선 = 임계값 −45 mV · 빨간 점선 = 충돌 시각)")
        vmin, vmax = -53.5, -43.5
        def X(tt): return x + int(tt / T * w)
        def Y(v): return y + int((vmax - v) / (vmax - vmin) * h)
        for xx in range(x, x + w, 12): pygame.draw.line(S, GRID, (xx, Y(c["v_th"])), (xx + 6, Y(c["v_th"])))
        s_end = min(int(t / dt), len(self.vgf) - 1); step = max(1, s_end // (w * 2))
        for col, ch in ((RED, 0), (ORANGE, 1)):
            idx = np.arange(0, s_end + 1, step)
            if idx.size >= 2:
                pts = [(X(i * dt), Y(float(self.vgf[i, ch]))) for i in idx]
                pygame.draw.lines(S, col, False, pts, 1)
        tc = X(m["t_c"])
        for yy in range(y, y + h, 10): pygame.draw.line(S, RED, (tc, yy), (tc, yy + 5))
        pygame.draw.line(S, WHITE, (X(t), y), (X(t), y + h), 1)
        for v in (-52, -48, -45):
            S.blit(self.font_s.render(f"{v}", True, DIM), (x - 34, Y(v) - 8))
        for tt in range(0, int(T) + 1, 100):
            S.blit(self.font_s.render(f"{tt}", True, DIM), (X(tt) - 8, y + h + 4))
        S.blit(self.font_s.render("ms", True, DIM), (x + w + 4, y + h + 4))
    def _plot_pop(self, S, x, y, w, h, t):
        m = self.meta; T = m["T"]
        self._axes(S, x, y, w, h, "뇌 전체의 발화 수 (1 ms 마다)")
        mx = max(int(self.pop.max()), 1); b = min(int(t), len(self.pop) - 1)
        bw = max(1, int(w / T))
        for i in range(b + 1):
            hh = int(self.pop[i] / mx * (h - 4))
            if hh > 0: pygame.draw.rect(S, (93, 109, 126), (x + int(i / T * w), y + h - hh, bw, hh))
        pygame.draw.line(S, WHITE, (x + int(t / T * w), y), (x + int(t / T * w), y + h), 1)
        S.blit(self.font_s.render(f"{mx}", True, DIM), (x - 34, y - 6)); S.blit(self.font_s.render("0", True, DIM), (x - 20, y + h - 8))
        for tt in range(0, int(T) + 1, 100):
            S.blit(self.font_s.render(f"{tt}", True, DIM), (x + int(tt / T * w) - 8, y + h + 4))
    # ---------------- 루프 ----------------
    def step_time(self):
        now = time.time(); dt_wall = now - self.last; self.last = now
        if self.hold_until is not None:
            if now >= self.hold_until:
                self.hold_until = None
                if self.auto:
                    self.k = self.k % 5 + 1; self.f = 0; self.game_t = 0.0; self._load_episode(); self.playing = True
            return
        if self.playing:
            self.game_t += dt_wall * 1000.0 / SLOWMOS[self.slow_i]
            self.f = int(self.game_t / self.pack.frame_ms)
            if self.f >= self.n_f:
                self.f = self.n_f - 1; self.game_t = self.f * self.pack.frame_ms; self.playing = False
                if self.auto: self.hold_until = now + 1.5
    def key(self, e):
        mods = pygame.key.get_mods(); shift = bool(mods & pygame.KMOD_SHIFT)
        if e.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
            self.k = int(e.unicode) if e.unicode in "12345" else self.k; self.f = 0; self.game_t = 0.0; self._load_episode(); self.playing = True; self.hold_until = None
        elif e.key == pygame.K_SPACE:
            if self.f >= self.n_f - 1: self.f = 0; self.game_t = 0.0
            self.playing = not self.playing; self.last = time.time()
        elif e.key in (pygame.K_RIGHT, pygame.K_LEFT):
            self.playing = False; self.f = int(np.clip(self.f + (1 if e.key == pygame.K_RIGHT else -1) * (10 if shift else 1), 0, self.n_f - 1)); self.game_t = self.f * self.pack.frame_ms
        elif e.key == pygame.K_LEFTBRACKET: self.slow_i = min(self.slow_i + 1, len(SLOWMOS) - 1)
        elif e.key == pygame.K_RIGHTBRACKET: self.slow_i = max(self.slow_i - 1, 0)
        elif e.key == pygame.K_HOME: self.f = 0; self.game_t = 0.0
        elif e.key == pygame.K_a:
            self.auto = not self.auto
            if self.auto: self.k = 1; self.f = 0; self.game_t = 0.0; self._load_episode(); self.playing = True
        elif e.key == pygame.K_h: self.help = not self.help
        elif e.key == pygame.K_s:
            fn = f"screenshot_k{self.k}_f{self.f}.png"; pygame.image.save(self.canvas, fn); print("saved", fn)
    def run(self):
        clock = pygame.time.Clock(); self.playing = True; self.last = time.time()
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: return
                    self.key(e)
                if e.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(e.size, pygame.RESIZABLE)
            self.step_time(); self.draw(); pygame.display.flip(); clock.tick(60)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default=os.path.join(resource_dir(), "pack"))
    ap.add_argument("--size", default="1600x900")
    ap.add_argument("--screenshot", nargs=3, metavar=("K", "FRAME", "OUT"), help="창 없이 한 프레임을 그려 저장(검사용)")
    a = ap.parse_args()
    if a.screenshot: os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init(); pygame.font.init()
    size = tuple(int(v) for v in a.size.lower().split("x"))
    pack = Pack(a.pack); pl = Player(pack, size, headless=bool(a.screenshot))
    if a.screenshot:
        k, fr, out = int(a.screenshot[0]), int(a.screenshot[1]), a.screenshot[2]
        pl.k = k; pl._load_episode(); pl.f = min(fr, pl.n_f - 1); pl.game_t = pl.f * pack.frame_ms; pl.draw(); pygame.image.save(pl.canvas, out); print("saved", out); return
    pl.run()

if __name__ == "__main__":
    main()
