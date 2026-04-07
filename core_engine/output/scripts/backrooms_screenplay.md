# 《困于后室》—— 电影分镜剧本
# "TRAPPED IN THE BACKROOMS" — Cinematic Script

> 基于 Backrooms Wiki 官方 Lore | 适配 kling/kling-v3-video-generation multi_shot 格式  
> 技术依据：Cinematic Script Writer v1.4.3 技术体系

---

## 角色设定（Character Bible）

**陈默**（男，26岁，城市探险爱好者）
- 外形：灰色卫衣，黑色工装裤，破旧帆布鞋，颈上挂着一台 Canon 胶片机
- 性格：沉默理性，但内心极易被孤独击溃
- 弧线：困惑 → 求生本能激活 → 理智崩溃边缘 → 意外获救

---

## 全局视觉风格（Global Visual Bible）

- **色彩分级**：去饱和黄绿色调，阴影压深至近黑，荧光区过曝泛白
- **镜头质感**：16mm 胶片颗粒，偶发竖条划痕，白平衡略偏冷
- **运动语言**：极慢推镜（dolly in）+ 手持轻微抖动；只有在心理崩溃时才出现剪辑加速
- **声音哲学**：荧光灯 hum 是全片底噪，从 40Hz 到 120Hz 随情绪波动；对白极少，均为自言自语

---

## 技术标注体系

| 缩写 | 含义 |
|------|------|
| ECU | 极近特写（Extreme Close-Up） |
| CU | 特写（Close-Up） |
| WS | 广角（Wide Shot） |
| POV | 第一人称视角 |
| DA | 荷兰斜角（Dutch Angle — disorientation） |
| SLO | 慢动作（Slow Motion） |
| RACK | 焦点切换（Rack Focus） |
| DIEGETIC | 画内声音（非配乐） |

---

## ACT I  「穿越」— *The Slip*

> **场景目标**：建立正常世界参照物，随后将其彻底摧毁
> **官方 Lore**：*"The most commonplace entrance into Level 0 is via The Frontrooms"*
> **Kling V3**：`model=kling/kling-v3-video-generation`, `mode=pro`, `audio=true`, `duration=10`

### SHOT 01 — 5s
**摄影**：POV 跟随 + 手持微抖 | **光线**：自然天窗逆光 | **色调**：正常白平衡（对比铺垫）

废弃购物中心。午后斜阳从天窗射入，落在灰扑扑的瓷砖上。POV 视角：陈默的相机镜头缓缓举起，对准走廊尽头一面被涂鸦覆盖的卷帘门，快门声「咔」——画面在取景框里定格了零点五秒，然后他迈步向前。一脚踏出，地板在接触的瞬间没有碎裂，而是像冷布丁一样无声地塌陷，他的腿膝盖以下没入地面，然后整个人被吞没。没有尖叫，只有相机脱手自由落体时取景框旋转的最后一帧——瓷砖天花板，一闪，黑。

**Kling V3 英文 prompt（Shot 01）**：
```
Found-footage POV shot. Abandoned shopping mall, afternoon sunlight streams through skylights onto cracked tiles.
POV follows a young man's camera viewfinder as he raises it to photograph a graffiti-covered shutter at corridor's end.
Shutter click — frame freezes for half a second. He steps forward.
The floor doesn't crack — it silently yields like cold pudding, his legs sink below the knee,
then his whole body is swallowed. No scream. Only the camera falling free,
the viewfinder frame spinning — tile ceiling, flash, black.
16mm film grain, natural white balance, handheld micro-shake, cinematic realism.
```

---

### SHOT 02 — 5s
**摄影**：极广角后拉（dolly out）| **光线**：不规则荧光灯，其中一组每隔约2秒闪烁 | **色调**：切入后室黄绿色调

陈默侧躺在潮湿米色地毯上，相机压在身下。WS 极广角仰视——他是走廊中央一个极小的人形，四面八方的走廊无限延伸至消失点，墙纸是发黄的箭头几何图案，无穷无尽重复。镜头缓缓向后拉远，他越来越小，直到他只是黄色洪流中的一粒灰尘。DIEGETIC：荧光灯低沉的嗡鸣声从远处涌来，像海浪，像呼吸。

**字幕叠入（fade in）**：`LEVEL 0 — "THE LOBBY"`
*Class 1 · Safe · Unstable · Devoid of Entities*

**Kling V3 英文 prompt（Shot 02）**：
```
Extreme wide angle dolly-out shot. A young man in grey hoodie lies on his side on worn, damp beige carpet.
Ultra-wide lens reveals an infinite corridor stretching in all directions to vanishing points.
Yellowed wallpaper with repeating arrow geometric patterns covers every wall identically.
Fluorescent tube lights at irregular intervals overhead — one group flickers every 2 seconds.
Camera slowly pulls back: the man becomes smaller and smaller, a speck in an ocean of yellow.
Desaturated yellow-green color grade. Deep shadow contrast. Fluorescent hum diegetic audio.
Title card fades in: LEVEL 0 — THE LOBBY. 16mm film grain, cinematic horror.
```

---

## ACT II  「漂移」— *The Drift*

> **场景目标**：展示非欧几里得空间的残酷逻辑，建立心理压力
> **官方 Lore**：*"It is possible to walk in a straight line, return to the starting point, and end up in a different set of rooms"*
> **Kling V3**：`model=kling/kling-v3-video-generation`, `mode=pro`, `audio=true`, `duration=10`

### SHOT 03 — 5s
**摄影**：平行跟随（tracking），镜头持续保持 DA 荷兰斜角约 8°
**光线**：单侧荧光打亮，另一侧压暗；投射长型条状阴影

陈默走在走廊中央，左手指尖持续轻触墙纸——不是恐惧，是为了确认自己在移动。地毯上，他刚才用鞋底划出的一个箭头——又出现在眼前了。他停步，蹲下来，用手指描了一遍那个箭头。然后站起来，转了180°，继续走——方向已经无法定义。

**Kling V3 英文 prompt（Shot 03）**：
```
Parallel tracking shot with persistent Dutch angle (8 degrees tilt). Young man in grey hoodie walks down
infinite corridor, left fingertips grazing the yellowed wallpaper as he moves — to confirm he is moving.
One-sided fluorescent key light, other side in deep shadow. Long stripe shadows on carpet.
The arrow he scratched with his shoe sole is directly in front of him again.
He stops. Silently crouches. Traces the arrow with his finger. Stands. Turns exactly 180 degrees. Continues walking.
Desaturated horror color grade, film grain, Dutch angle camera.
```

---

### SHOT 04 — 5s
**摄影**：RACK FOCUS，焦点从陈默的脸切换至墙面文字
**光线**：插入式画外手电（motivated source），照出墙上字迹

他停在一面墙前。墙纸表面密密麻麻的字迹，至少四个不同笔迹的层叠，如同地质年代剖面图。最新的是黑色马克笔："**不要相信右转。灯在撒谎。向前走。不要睡着。**" 他举起相机拍照，看屏幕——只是一面空白的黄色墙纸。他回头看真实的墙，字迹还在。他的手指颤抖，触碰那些字。

**Kling V3 英文 prompt（Shot 04）**：
```
Rack focus shot shifting between man's face and wall text. Wall covered in layered handwriting —
at least four different pen styles stratigraphy, oldest faded, newest in black marker:
"DO NOT TRUST RIGHT TURNS. THE LIGHTS LIE. KEEP WALKING. DON'T SLEEP."
He photographs it with his camera. Checks screen: blank yellow wall, no text.
Looks back at real wall: text still there. ECU his trembling fingers touching the indentations.
Motivated flashlight source lighting. Desaturated horror grade, rack focus cinematography.
```

---

## ACT III  「幻觉」— *The Hallucination*

> **场景目标**：Level 0 的核心恐怖——不是怪物，是自我的镜像
> **官方 Lore**：*"rare cases reporting wanderers descending into utter lunacy as a result of the level's properties"*
> **Kling V3**：`model=kling/kling-v3-video-generation`, `mode=pro`, `audio=true`, `duration=10`

### SHOT 05 — 5s
**摄影**：长焦压缩（telephoto compression），画面失去纵深感
**光线**：走廊纵深逐渐减光，远端近乎黑暗

走廊尽头，一个背影。灰色卫衣，黑色背包，颈上挂着相机——和陈默一模一样。他叫了一声「喂——」，声音在走廊里怪异地折回。那个身影没有反应，转过拐角。陈默追了上去——走廊空无一人，只有一组荧光灯正在剧烈闪烁。他低头看地毯：只有他自己的脚印。

**Kling V3 英文 prompt（Shot 05）**：
```
Telephoto compression shot — depth of field flattened, near and far appear same size.
At the far end of the corridor: a figure. Grey hoodie, black backpack, camera around neck — identical to protagonist.
He calls out. His voice echoes back before reaching the figure. The figure doesn't respond, turns a corner.
He chases. Rounds the corner: empty corridor. Only one group of fluorescent lights strobing violently.
He looks at the carpet: only his own footprints exist.
Telephoto lens compression, cinematic horror, desaturated green-yellow color grade.
```

---

### SHOT 06 — 5s
**摄影**：固定机位 + ECU 面部，轻微推进
**光线**：闪烁荧光灯制造 2fps 的间歇黑暗，仿佛胶片放映机卡带

陈默靠着墙滑坐在地上，双手捂脸，嗡鸣声攀升至接近痛苦的频率。他放下手，睁开眼——眼睛充血，瞳孔散大，目光失焦。嘴唇开始动，喃喃地读墙上的字：「向前走……任何方向……都是向前……」荧光灯全部熄灭，0.3 秒完全黑场。然后重新亮起——他已经站起来，表情平静到不像话，面向走廊深处。

**Kling V3 英文 prompt（Shot 06）**：
```
Fixed camera ECU slowly pushing in on face. He slides down the wall onto the floor, hands over face.
Fluorescent hum climbs to near-painful pitch. He lowers his hands:
bloodshot eyes, slightly dilated pupils, unfocused gaze. Lips moving barely audible:
"Keep walking... any direction... is forward..."
All fluorescent lights cut out simultaneously — 0.3 seconds of absolute blackness.
Lights flicker back: he is standing. Expression unnaturally calm. Facing the corridor's depth.
Strobing fluorescent light like a broken film projector. ECU cinematic horror push-in.
```

---

## ACT IV  「马尼拉室 / 出口」— *The Manila Room*

> **场景目标**：以官方 Lore 中的神秘房间作为救赎，但留有未解之谜
> **官方 Lore**：*"The Manila Room — serves as an exit to Level 1. A soothing feeling. Orange-tinted light."*
> **Kling V3**：`model=kling/kling-v3-video-generation`, `mode=pro`, `audio=true`, `duration=10`

### SHOT 07 — 5s
**摄影**：OTS（过肩跟随），镜头略微仰视
**光线**：从前方拐角透出橙色暖光——与全片荧光白绿成鲜明对比

陈默停下脚步，轻轻嗅了一口。嗡鸣声第一次出现轻微的下降。他循着拐角走去，拐角处的光是橙黄色的，温暖的。他推开虚掩的门：房间极小，四面墙上是马尼拉信封一样的奶黄色小圆点壁纸。天花板只有一盏灯，橙黄色，昏暗，安静，像回到了家里的客厅。房间中央有一把椅子。椅子上放着一个旧帆布背包，还有一张折叠的便条纸。

**Kling V3 英文 prompt（Shot 07）**：
```
Over-the-shoulder shot, camera slightly below eye level. He stops mid-corridor, takes a deep slow breath.
The fluorescent hum drops slightly for the first time. Warm orange-amber light emanates from a slightly-open door ahead —
completely contrasting with the white-green fluorescent horror throughout.
He pushes the door open: a tiny room, walls covered in manila-paper small-dot wallpaper,
one single orange-tinted overhead lamp, dim and warm and quiet, like coming home.
A chair. On the chair: an old canvas backpack and a folded note.
Warm orange cinematography, intimate horror contrast, over-the-shoulder framing.
```

---

### SHOT 08 — 5s
**摄影**：固定机位从门缝往内 + 最终 SLO 慢动作
**光线**：橙光充满画面，到结尾墙壁开始轻微发光

他坐下，展开便条，读出声：「**在这里等。不要睡着。等到地板变温。然后走进墙。不要犹豫。**」他攥紧便条纸。镜头从门缝缓缓退远。他站起来，手掌贴在后墙上——墙面透出淡淡的光，像冻住的湖面下有鱼在游动。他闭眼，向前一步。SLO：身体穿透墙壁，最后只剩下一只手贴着发光的墙纸，然后消失。

**字幕淡入（slow fade）**：`LEVEL 1 — "THE HABITABLE ZONE"`
*Class 1 · Safe · Secure · Entity Presence: Confirmed*
*You made it out. But you are not alone.*

**Kling V3 英文 prompt（Shot 08）**：
```
Fixed camera peering through door crack into the Manila Room. He sits in the chair,
unfolds a note, reads aloud barely audible: "Wait here. Don't sleep. When the floor warms — walk into the wall.
Don't hesitate." He clutches the note. Camera slowly retreats through the door crack.
He stands. Palms flat against the back wall. The wall begins to glow faintly,
like light through ice over dark water. He closes his eyes. Steps forward.
SLOW MOTION: his body passes through the wall. Last image: one hand on the glowing wallpaper,
five fingers spread, luminous — then gone.
Title card slow fade: LEVEL 1 — THE HABITABLE ZONE. "You made it out. But you are not alone."
Cinematic horror, warm amber finale, 16mm film grain slow motion.
```

---

## 制作参数总表（Kling V3 Production Sheet）

| 幕次 | Shot | multi_prompt index | 时长 | mode | audio | aspect |
|------|------|-------------------|------|------|-------|--------|
| ACT I 穿越 | 01 | 1 | 5s | pro | true | 16:9 |
| ACT I 穿越 | 02 | 2 | 5s | pro | true | 16:9 |
| ACT II 漂移 | 03 | 1 | 5s | pro | true | 16:9 |
| ACT II 漂移 | 04 | 2 | 5s | pro | true | 16:9 |
| ACT III 幻觉 | 05 | 1 | 5s | pro | true | 16:9 |
| ACT III 幻觉 | 06 | 2 | 5s | pro | true | 16:9 |
| ACT IV 马尼拉室 | 07 | 1 | 5s | pro | true | 16:9 |
| ACT IV 马尼拉室 | 08 | 2 | 5s | pro | true | 16:9 |

**总时长**：40s（4幕 × 10s）
**模型**：`kling/kling-v3-video-generation`
**端点**：`POST https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis`
**区域**：中国内地（北京），同一 `DASHSCOPE_API_KEY`

---

## 字幕文本（SRT）

```srt
1
00:00:00,000 --> 00:00:10,000
[穿越] 地板像冷布丁一样塌陷。
你来到了一个你从未离开过的地方。

2
00:00:10,000 --> 00:00:20,000
LEVEL 0 — "THE LOBBY"
向前走。任何方向都是向前。

3
00:00:20,000 --> 00:00:30,000
[幻觉] 他和你穿着一样的衣服。
他的脚印不存在。

4
00:00:30,000 --> 00:00:40,000
LEVEL 1 — "THE HABITABLE ZONE"
你出来了。但你不是一个人。
```
