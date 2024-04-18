import math
from PIL import Image


WIDTH: int = 320
HEIGHT: int = 240
N_PIXELS: int = WIDTH * HEIGHT

TEXTURE_PATH: str = 'C:/Users/bean/Desktop/test-texture.png'
PNG_SAVE_PATH: str = 'C:/Users/bean/Desktop/cpu-triangle.png'


class Vec2:
    x: float
    y: float

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    @staticmethod
    def scalar(s: float):
        return Vec2(s, s)

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y

    def __mul__(self, other):
        return Vec2(self.x * other.x, self.y * other.y)

    def __imul__(self, other):
        self.x *= other.x
        self.y *= other.y

    def __truediv__(self, other):
        return Vec2(self.x / other.x, self.y / other.y)

    def __idiv__(self, other):
        self.x /= other.x
        self.y /= other.y

    def __neg__(self):
        return Vec2(-self.x, -self.y)


class Vec3:
    x: float
    y: float
    z: float

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def scalar(s: float):
        return Vec3(s, s, s)

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z

    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z

    def __mul__(self, other):
        return Vec3(self.x * other.x, self.y * other.y, self.z * other.z)

    def __imul__(self, other):
        self.x *= other.x
        self.y *= other.y
        self.z *= other.z

    def __truediv__(self, other):
        return Vec3(self.x / other.x, self.y / other.y, self.z / other.z)

    def __idiv__(self, other):
        self.x /= other.x
        self.y /= other.y
        self.z /= other.z

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)


class Triangle:
    v: tuple[Vec2, Vec2, Vec2]
    v_col: tuple[Vec3, Vec3, Vec3]
    v_uv: tuple[Vec2, Vec2, Vec2]

    def __init__(
        self,
        v: tuple[Vec2, Vec2, Vec2],
        v_col: tuple[Vec3, Vec3, Vec3],
        v_uv: tuple[Vec2, Vec2, Vec2]
    ) -> None:
        self.v = v
        self.v_col = v_col
        self.v_uv = v_uv

    def cart_to_bary(self, p: Vec2) -> Vec3:
        return cart_to_bary(p, self.v[0], self.v[1], self.v[2])


# |a| * |b| * sin(theta)
def cross_2d(a: Vec2, b: Vec2) -> float:
    return (a.x * b.y) - (a.y * b.x)


# triangle vertices must be ordered counterclockwise
def cart_to_bary(
    p: Vec2,
    v0: Vec2,
    v1: Vec2,
    v2: Vec2
) -> Vec3:
    b = Vec3(
        cross_2d(v1 - p, v2 - p),
        cross_2d(v2 - p, v0 - p),
        cross_2d(v0 - p, v1 - p)
    )
    b /= Vec3.scalar(cross_2d(v1 - v0, v2 - v0))
    return b


def bary_is_outside(b: Vec3) -> bool:
    return min(b.x, b.y, b.z) < 0


def idx_to_icoord(idx: int, width: int) -> tuple[int, int]:
    return (idx % width, idx // width)


def icoord_to_idx(x: int, y: int, width: int) -> int:
    return x + (y * width)


def mix(a: float, b: float, t: float) -> float:
    return a + t * (b - a)


def mix_vec2(a: Vec2, b: Vec2, t: float) -> Vec2:
    return a + Vec2.scalar(t) * (b - a)


def mix_vec3(a: Vec3, b: Vec3, t: float) -> Vec3:
    return a + Vec3.scalar(t) * (b - a)


def mix_bilinear(
    bl: float,  # value at the bottom left
    br: float,  # bottom right
    tl: float,  # top left
    tr: float,  # top right
    t_horz: float,  # blend weight from left to right
    t_vert: float  # blend weight from bottom to top
) -> float:
    return mix(
        mix(bl, br, t_horz),
        mix(tl, tr, t_horz),
        t_vert
    )


def mix_vec2_bilinear(
    bl: Vec2,  # value at the bottom left
    br: Vec2,  # bottom right
    tl: Vec2,  # top left
    tr: Vec2,  # top right
    t_horz: float,  # blend weight from left to right
    t_vert: float  # blend weight from bottom to top
) -> float:
    return mix_vec2(
        mix_vec2(bl, br, t_horz),
        mix_vec2(tl, tr, t_horz),
        t_vert
    )


def mix_vec3_bilinear(
    bl: Vec3,  # value at the bottom left
    br: Vec3,  # bottom right
    tl: Vec3,  # top left
    tr: Vec3,  # top right
    t_horz: float,  # blend weight from left to right
    t_vert: float  # blend weight from bottom to top
) -> float:
    return mix_vec3(
        mix_vec3(bl, br, t_horz),
        mix_vec3(tl, tr, t_horz),
        t_vert
    )


def texel_fetch(
    tex: Image,
    tex_data: list[tuple[int, int, int]],
    icoord: tuple[int, int]
) -> Vec3:
    if icoord[0] < 0:
        icoord = (0, icoord[1])
    if icoord[0] >= tex.width:
        icoord = (tex.width - 1, icoord[1])

    if icoord[1] < 0:
        icoord = (icoord[0], 0)
    if icoord[1] >= tex.height:
        icoord = (icoord[0], tex.height - 1)

    idx = icoord_to_idx(
        icoord[0],
        icoord[1],
        tex.width
    )

    col_rgb8: tuple[int, int, int] = tex_data[idx]
    return Vec3(
        col_rgb8[0] / 255.,
        col_rgb8[1] / 255.,
        col_rgb8[2] / 255.
    )


# create buffer and initialize all colors to black
buf: list[Vec3] = []
for i in range(N_PIXELS):
    buf.append(Vec3.scalar(0))

# triangle list
tris: list[Triangle] = []
tris.append(Triangle(
    v=(
        Vec2(0, 0),
        Vec2(320, 0),
        Vec2(0, 240)
    ),
    v_col=(
        Vec3(.1, .2, .9),
        Vec3(.9, .4, .1),
        Vec3(.2, .7, .1)
    ),
    v_uv=(
        Vec2(0, 1),
        Vec2(1, 1),
        Vec2(0, 0)
    )
))
tris.append(Triangle(
    v=(
        Vec2(320, 0),
        Vec2(320, 240),
        Vec2(0, 240)
    ),
    v_col=(
        Vec3(.9, .4, .1),
        Vec3(.9, .1, .6),
        Vec3(.2, .7, .1)
    ),
    v_uv=(
        Vec2(1, 1),
        Vec2(1, 0),
        Vec2(0, 0)
    )
))

# load the texture
tex = Image.open(TEXTURE_PATH).convert(mode='RGB')
tex_data: list[tuple[int, int, int]] = list(tex.getdata())

# render
for y in range(HEIGHT):
    for x in range(WIDTH):
        p = Vec2(x + .5, y + .5)

        col = Vec3(.1, .1, .1)
        for tri in tris:
            bary: Vec3 = tri.cart_to_bary(p)
            if bary_is_outside(bary):
                continue

            interp_col: Vec3 = \
                (Vec3.scalar(bary.x) * tri.v_col[0]) \
                + (Vec3.scalar(bary.y) * tri.v_col[1]) \
                + (Vec3.scalar(bary.z) * tri.v_col[2])

            interp_uv: Vec2 = \
                (Vec2.scalar(bary.x) * tri.v_uv[0]) \
                + (Vec2.scalar(bary.y) * tri.v_uv[1]) \
                + (Vec2.scalar(bary.z) * tri.v_uv[2])

            sample_point: Vec2 = interp_uv * Vec2(tex.width, tex.height)

            icoord_bl = (
                int(math.floor(sample_point.x - .5)),
                int(math.floor(sample_point.y - .5))
            )
            icoord_br = (icoord_bl[0] + 1, icoord_bl[1] + 0)
            icoord_tl = (icoord_bl[0] + 0, icoord_bl[1] + 1)
            icoord_tr = (icoord_bl[0] + 1, icoord_bl[1] + 1)

            col_bl: Vec3 = texel_fetch(tex, tex_data, icoord_bl)
            col_br: Vec3 = texel_fetch(tex, tex_data, icoord_br)
            col_tl: Vec3 = texel_fetch(tex, tex_data, icoord_tl)
            col_tr: Vec3 = texel_fetch(tex, tex_data, icoord_tr)

            bl_center = Vec2(
                icoord_bl[0] + .5,
                icoord_bl[1] + .5
            )
            bilinear_offs: Vec2 = sample_point - bl_center

            col: Vec3 = mix_vec3_bilinear(
                col_bl,
                col_br,
                col_tl,
                col_tr,
                t_horz=bilinear_offs.x,
                t_vert=bilinear_offs.y
            )

        idx = icoord_to_idx(x, HEIGHT - y - 1, WIDTH)
        buf[idx] = col

# RGB8 buffer
buf_rgb8: list[tuple[int, int, int]] = []
for i in range(N_PIXELS):
    col: Vec3 = buf[i]
    buf_rgb8.append((
        int(col.x * 255),
        int(col.y * 255),
        int(col.z * 255)
    ))

# export to PNG
img: Image = Image.new('RGB', (WIDTH, HEIGHT))
img.putdata(buf_rgb8)
img.save(PNG_SAVE_PATH, 'PNG')
