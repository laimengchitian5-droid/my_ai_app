# ============================================================
# このファイルは、AIアプリの「本体（ほんたい）」です
# やっていることは、つぎの3つだけです
# 1. 人が書いた商品の情報を、ホームページで受け取る
# 2. その情報を、無料のGroq（グロック）のAIに送る
# 3. できた商品説明を、もういちどホームページに見せる
# ------------------------------------------------------------
# 【あとでやること】ひみつの合言葉は、このファイルには書きません
# 同じフォルダに「.env」という隠し部屋ファイルを作り、
# 中に  GROQ_API_KEY=gsk_自分の鍵  と1行だけ書いてください
# ============================================================

# FastAPI（ファストエーピーアイ）は、ホームページや受付窓口を作る道具です
from fastapi import FastAPI
# Form は、画面の入力らんから送られてきた文字を受け取る道具です
from fastapi import Form
# HTMLResponse は、「文字データ」ではなく「ホームページ」を返す道具です
from fastapi.responses import HTMLResponse
# Groq は、無料で使えるAIに話しかけるための道具です
from groq import Groq
# load_dotenv は、「.env」という隠し部屋から合言葉を読み取る道具です
from dotenv import load_dotenv
# os は、パソコンの中の設定（かんきょうへんすう）を見る道具です
import os
# html は、悪い文字がページを壊さないように、安全な文字へ変える道具です
import html
# uvicorn は、このアプリを実際に動かして受付を始める道具です
import uvicorn

# 「.env」という隠し部屋ファイルを開いて、中身をメモリーに読み込みます
load_dotenv()

# FastAPIのアプリ本体を作ります。これから先の受付ルールは、全部この app に書きます
app = FastAPI(title="AI商品説明作成ツール（マルチSNS対応）")

# 隠し部屋から「GROQ_API_KEY」という名前の合言葉を取り出します（なければ None になります）
groq_api_key = os.getenv("GROQ_API_KEY")

# 合言葉があるときだけ、AIに話しかける係（Groqクライアント）を作ります
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

# 使うAIの名前です。無料で速く、何度も試しやすいモデルを選びます
GROQ_MODEL = "llama-3.1-8b-instant"

# AIへの役割と、日本語の絶対ルールをまとめた指示文です（role: system で渡します）
SYSTEM_MESSAGE = """
あなたは、日本の高級ブランドと丁寧なネットショップで大活躍している天才コピーライターです。
渡された商品情報だけを根拠に、20〜30代のビジネスパーソンが思わず欲しくなる商品説明を書いてください。

【ことばづかい】
・文末は必ず「です」「ます」の優しい丁寧語にする。
・「〜である」「〜だ」「〜される」「〜となっている」は使わない。カタログ調・説明書調は禁止。
・人に話しかけるように、やわらかく、はっきり書く。

【書き方の核心】
・「軽い」「広い」などの特徴だけで終わらせない。
・必ず「だから、使う人の毎日がどう良くなるか」まで書く。
・良い例: 「とても軽いです。だから毎日の通勤がラクになります。」
・悪い例: 「軽量である。」「軽さが特徴です。」（未来が見えない）
・魅力は「特徴 → だから → 明るい未来」の順で、1つずつ書く。

【絶対ルール】
1. 出力はすべて、ネイティブが書いたような自然で美しい日本語だけにする。
2. 英語・中国語・ヒンディー語・ハングルなど、外国語の単語や文を混ぜない。商品名や素材名に外国語が含まれるときだけ、その部分はそのまま残す。
3. 「〜味相しまちがい」のような、存在しない日本語、誤変換、機械翻訳調、意味の通らない熟語は絶対に禁止。
4. です・ます調で最後まで統一する。途中でタメ口や「だ・である」調に切り替えない。
5. カタカナ英語の連発（イノベーティブ、ラグジュアリー、エッセンス など）は使わない。どうしても必要な場合だけ、ごく少数にする。
6. 入力に無い素材・効果・受賞歴・数字は作らない。誇大広告や根拠のない最上級（絶対、世界一、必見）は使わない。
7. 前置き（かしこまりました、了解です など）や英語の見出しは書かない。完成原稿だけを出す。
8. 絵文字とハッシュタグは、選ばれたSNSの追加ルールに従う。追加ルールが無いときは絵文字を使わない。

【出力の形】
選ばれたSNSに追加ルールがあるときは、そちらの形を最優先する。
追加ルールが無いとき（通常）だけ、次の形にする。
キャッチコピー（1行。使う人の明るい未来が想像できること）
3つの魅力（どれも「特徴。だから〜になります。」の形）
商品説明の本文（2〜4段落。ですます調。未来の場面が目に浮かぶこと）
出品用の短い紹介（3行以内。ですます調）
"""

# メルカリ用が選ばれたときだけ、AIへの指示に足す追加ルールです
MERCARI_RULES = """
【メルカリ用の追加ルール】
・購入者が安心できるように、商品の状態と梱包方法（丁寧な発送）についての文言を、本文の中に自然に入れてください。
・状態は、入力にある事実だけを使います。分からない傷や欠点は作らないでください。入力に状態が無いときは、「目立つ傷はなく、丁寧に保管していました」のように、盛りすぎない安心の一文にしてください。
・梱包は、「緩衝材で包み、丁寧に発送します」など、届くまでの心配が減る言い方を自然に入れてください。別枠の注意書きではなく、本文の流れの中で書いてください。
・売れやすくなるハッシュタグを、ちょうど10個、いちばん下に自動で生成してください。
・ハッシュタグは日本語中心で、商品の種類・素材・用途・検索されやすい言葉にします。不自然な英語タグの羅列はしません。
・ハッシュタグの前に、空行を1つ入れてから書いてください。
"""

# X（旧Twitter）用が選ばれたときだけ、AIへの指示に足す追加ルールです
X_RULES = """
【X（旧Twitter）用の追加ルール】
・出力は、コピーしてすぐ投稿できる文を1本だけにしてください。見出しや説明は書かない。
・140文字以内が絶対の文字数制限です。空白・改行・ハッシュタグも含めて、141文字以上は禁止です。
・思わずリポストやいいねしたくなる、バズるキャッチコピーにしてください。短く、リズムよく、余韻を残します。
・特徴だけで終わらず、使う人の明るい未来が一瞬で伝わるようにします。
・関連するハッシュタグは2個だけ厳選し、文の末尾につけてください。3個以上は禁止です。
・絵文字は使いません。外国語も混ぜません。
・140文字に収めるため、長い説明・箇条書き・本文パートは書かないでください。
"""

# Instagram用が選ばれたときだけ、AIへの指示に足す追加ルールです
INSTAGRAM_RULES = """
【Instagram用の追加ルール】
・この出力では、絵文字を使わないルールは適用しません。
・文章のあちこちに、内容に合ったオシャレな絵文字をたくさん散りばめてください。意味のない連打はせず、世界観に合うものを選びます。
・ですます調は守りつつ、保存したくなる上品なキャプションにします。
・特徴だけで終わらず、「だから毎日がこう良くなる」まで書いてください。
・本文のあとに空行を1つ入れ、ハッシュタグをちょうど20個、改行を挟んで綺麗に並べてください。
・ハッシュタグは1行に3〜5個ずつ、見やすく改行します。20個より多くても少なくてもいけません。
・ハッシュタグは日本語中心で、商品の種類・素材・世界観・用途が検索されるようにします。不自然な英語タグの羅列はしません。
・前置きは書かず、キャプション本文とハッシュタグだけを出します。
"""

# 選ばれた出力先ごとに、足すルール・お願い文・結果カードの名前をまとめます
CHANNEL_SETTINGS = {
    "standard": {
        "extra_rules": "",
        "user_intro": "次の商品情報だけで、ルールを守った商品説明を作ってください。",
        "kicker": "Finished Copy",
        "title": "完成した商品説明",
    },
    "mercari": {
        "extra_rules": MERCARI_RULES,
        "user_intro": "メルカリ出品用の商品説明を作ってください。メルカリ用の追加ルールも守ってください。",
        "kicker": "Mercari",
        "title": "メルカリ用の商品説明",
    },
    "x": {
        "extra_rules": X_RULES,
        "user_intro": "X（旧Twitter）投稿用の文を作ってください。140文字以内と、ハッシュタグ2個のルールを絶対に守ってください。",
        "kicker": "X",
        "title": "X用の投稿文",
    },
    "instagram": {
        "extra_rules": INSTAGRAM_RULES,
        "user_intro": "Instagram投稿用のキャプションを作ってください。オシャレな絵文字と、ハッシュタグ20個のルールを守ってください。",
        "kicker": "Instagram",
        "title": "Instagram用の投稿文",
    },
}

# この関数は、画面に出すホームページの文章（HTML）を組み立てます
def make_html_page(question="", answer="", error_message="", output_type="standard"):
    # 人が書いた文字を、そのままページに入れると危険なので、安全な文字に変えます
    safe_question = html.escape(question)
    # AIの返事も同じように、安全な文字へ変えます
    safe_answer = html.escape(answer)
    # 失敗の文章も、安全な文字へ変えます
    safe_error = html.escape(error_message)
    # 返事の改行（Enter）を、画面でも改行して見えるように変えます
    safe_answer_with_breaks = safe_answer.replace("\n", "<br>")
    # 失敗メッセージがあるときだけ、注意の箱のHTMLを作ります。なければ空文字です
    error_box = f'<p class="error">{safe_error}</p>' if safe_error else ""
    # 知らない出力先が来たときは、通常モードに戻します
    if output_type not in CHANNEL_SETTINGS:
        output_type = "standard"
    # 選ばれたSNSの、結果カード用の名前を取り出します
    channel = CHANNEL_SETTINGS[output_type]
    # 返事があるときだけ、完成原稿の箱のHTMLを作ります。なければ空文字です
    answer_box = (
        # 完成した文章を、高級なカードの中に入れます
        f'<section class="panel result"><p class="panel-kicker">{channel["kicker"]}</p><h2>{channel["title"]}</h2><div class="result-body">{safe_answer_with_breaks}</div></section>'
        # 返事の文字が入っているときだけ、上のカードを使います
        if safe_answer
        # 返事がまだ無いときは、空の文字にしてカード自体を出しません
        else ""
    )
    # 選ばれているボタンに checked をつけ、それ以外は空にします
    standard_checked = "checked" if output_type == "standard" else ""
    # メルカリ用が選ばれているときです
    mercari_checked = "checked" if output_type == "mercari" else ""
    # X用が選ばれているときです
    x_checked = "checked" if output_type == "x" else ""
    # Instagram用が選ばれているときです
    instagram_checked = "checked" if output_type == "instagram" else ""
    # ここから下が、ブラウザに見せるホームページの中身です
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <!-- 日本語の文字化けを防ぐ設定です -->
  <meta charset="UTF-8">
  <!-- スマホでも見やすい大きさにする設定です -->
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- ブラウザのタブに出る名前です -->
  <title>AI商品説明作成ツール｜マルチSNS対応</title>
  <!-- 高級感のある見出し用フォントと、本文用フォントを読み込みます -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <!-- フォントを速く読み始めるための準備です -->
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <!-- 英語のセリフ体と、日本語の明朝・ゴシックを読みます -->
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Noto+Sans+JP:wght@400;500;600&family=Noto+Serif+JP:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    /* よく使う色に、わかりやすい名前をつけます */
    :root {{
      --bg: #0c0b0a; /* いちばん濃い背景色（高級な黒） */
      --bg-soft: #161412; /* 少し明るい黒 */
      --gold: #c9a56a; /* ボタンや飾りに使う金色 */
      --gold-soft: #e8d5a8; /* 明るい金色（文字用） */
      --line: rgba(201, 165, 106, 0.28); /* 細い金のわく線 */
      --text: #f6f1e8; /* 本文の明るい文字色 */
      --muted: #b7ae9f; /* 説明文のやわらかい色 */
      --panel: rgba(22, 20, 18, 0.88); /* カードの半透明な黒 */
    }}
    /* 箱の大きさを、わく線まで含めて計算します */
    * {{ box-sizing: border-box; }}
    /* ページ全体の見た目です */
    body {{
      margin: 0; /* 外側の余白をなくします */
      min-height: 100vh; /* 画面の高さいっぱい使います */
      font-family: "Noto Sans JP", sans-serif; /* 本文は読みやすいゴシック体です */
      color: var(--text); /* 文字を明るい色にします */
      background-color: var(--bg); /* 背景を高級な黒にします */
      /* 中央にやわらかい金の光を置いて、奥行きを出します */
      background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(201, 165, 106, 0.18), transparent 55%),
        linear-gradient(180deg, #141210 0%, #0c0b0a 42%, #0a0908 100%);
    }}
    /* 画面いちばん上の、大きなタイトルエリアです */
    .hero {{
      text-align: center; /* 文字を左右の真ん中にします */
      padding: 72px 24px 48px; /* 上下にたっぷり余白をとります */
      border-bottom: 1px solid var(--line); /* 下に細い金の線を引きます */
    }}
    /* タイトルの上の、小さな英語ラベルです */
    .eyebrow {{
      margin: 0 0 18px; /* 下に余白をあけます */
      font-family: "Cormorant Garamond", serif; /* 英語らしい上品な字体です */
      font-size: 0.85rem; /* 小さめの文字です */
      letter-spacing: 0.42em; /* 文字と文字の間を広げます */
      color: var(--gold); /* 金色にします */
      text-transform: uppercase; /* 全部大文字にします */
    }}
    /* 画面いちばん上の、デカデカしたタイトルです */
    .hero h1 {{
      margin: 0; /* 余分な余白をなくします */
      font-family: "Noto Serif JP", "Cormorant Garamond", serif; /* 高級感のある明朝体です */
      font-size: clamp(2.8rem, 8vw, 5.6rem); /* 画面の大きさに合わせて超大きくします */
      font-weight: 600; /* 少し太くします */
      letter-spacing: 0.12em; /* 文字間を広げて看板らしくします */
      line-height: 1.2; /* 2行になっても窮屈にしない行間です */
      color: var(--gold-soft); /* 明るい金色の文字にします */
    }}
    /* タイトルの下の、短いキャッチコピーです */
    .hero-sub {{
      margin: 22px auto 0; /* 上に余白をあけ、左右真ん中に置きます */
      max-width: 520px; /* 長くなりすぎないようにします */
      color: var(--muted); /* 本文より少し弱い色にします */
      letter-spacing: 0.12em; /* 字間を少し広げます */
      font-size: 0.95rem; /* 読みやすい大きさです */
    }}
    /* タイトルの下の細い飾り線です */
    .gold-rule {{
      width: 72px; /* 短い線の長さです */
      height: 1px; /* とても細い線です */
      margin: 28px auto 0; /* 中央に置きます */
      background: var(--gold); /* 金色にします */
    }}
    /* 真ん中の本文エリアです */
    main {{
      max-width: 820px; /* 横幅が広くなりすぎないようにします */
      margin: 0 auto; /* 左右の真ん中に置きます */
      padding: 48px 20px 80px; /* まわりの余白です */
    }}
    /* 入力カードや結果カードの共通デザインです */
    .panel {{
      background: var(--panel); /* 半透明の黒いカードです */
      border: 1px solid var(--line); /* 細い金のわく線です */
      border-radius: 4px; /* 角は少しだけ丸くして、まじめな印象にします */
      padding: 32px; /* 中の余白を広めにします */
      margin-bottom: 24px; /* 下のカードとのすき間です */
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35); /* やわらかい影をつけます */
    }}
    /* カードの左上の小さな英語ラベルです */
    .panel-kicker {{
      margin: 0 0 8px; /* 下に少し余白をあけます */
      font-family: "Cormorant Garamond", serif; /* 上品な英語フォントです */
      color: var(--gold); /* 金色にします */
      letter-spacing: 0.28em; /* 字間を広げます */
      font-size: 0.78rem; /* 小さめです */
      text-transform: uppercase; /* 大文字にします */
    }}
    /* カードの中の見出しです */
    .panel h2 {{
      margin: 0 0 20px; /* 下に余白をあけます */
      font-family: "Noto Serif JP", serif; /* 明朝体で高級感を出します */
      font-size: 1.35rem; /* 読みやすい見出しサイズです */
      font-weight: 600; /* 少し太くします */
      letter-spacing: 0.08em; /* 字間を少し広げます */
    }}
    /* 入力らんの上のラベル（説明）です */
    label {{
      display: block; /* 1行まるごと使います */
      font-weight: 500; /* 少し太くします */
      margin-bottom: 10px; /* 入力らんとのすき間です */
      color: var(--gold-soft); /* 明るい金色にします */
      letter-spacing: 0.06em; /* 字間です */
    }}
    /* 商品情報を書く大きな入力らんです */
    textarea {{
      width: 100%; /* 横いっぱいに広げます */
      min-height: 180px; /* 最初の高さを確保します */
      padding: 16px 18px; /* 文字のまわりの余白です */
      border: 1px solid var(--line); /* 金のわく線です */
      border-radius: 2px; /* 角はほぼ四角です */
      font-size: 1rem; /* 読みやすい文字サイズです */
      font-family: inherit; /* ページと同じ字体にします */
      resize: vertical; /* 上下にだけ大きさを変えられます */
      color: var(--text); /* 入力文字を明るくします */
      background: rgba(0, 0, 0, 0.28); /* 入力らんの中を少し暗くします */
      outline: none; /* ブラウザ標準の青い枠は消し、自分の色を使います */
      line-height: 1.8; /* 行間を広げて読みやすくします */
    }}
    /* 入力らんをクリックしたときの見た目です */
    textarea:focus {{
      border-color: var(--gold); /* わく線をはっきりした金色にします */
      box-shadow: 0 0 0 3px rgba(201, 165, 106, 0.15); /* うすい金の光をつけます */
    }}
    /* 出力先（通常 / メルカリ / X / Instagram）を選ぶボタンの並びです */
    .channel-row {{
      display: grid; /* きれいに格子状に並べます */
      grid-template-columns: 1fr 1fr; /* 横に2つずつ、全部で4つのボタンです */
      gap: 12px; /* ボタン同士のすき間です */
      margin: 8px 0 4px; /* 上下の余白です */
    }}
    /* 本物のラジオボタンは隠して、見た目のボタンだけ見せます */
    .channel-row input {{
      position: absolute; /* 画面の位置から外します */
      opacity: 0; /* 見えなくします */
      pointer-events: none; /* クリックはラベル側で受けます */
    }}
    /* 「出力の種類」など、入力の上の見出しラベルです */
    .field-label {{
      margin-top: 22px; /* 上の入力らんとのすき間です */
    }}
    /* 1つの選択肢ボタンです */
    .channel {{
      flex: none; /* 格子のマスいっぱいにします */
      min-width: 0; /* 文字がはみ出してもマスを壊さないようにします */
      width: 100%; /* マスの横幅いっぱいにします */
      cursor: pointer; /* マウスを指の形にします */
      margin-bottom: 0; /* 全体の label 余白を打ち消します */
    }}
    /* 選択肢の見た目（まだ選んでいないとき）です */
    .channel span {{
      display: block; /* 箱として広げます */
      text-align: center; /* 文字を中央にします */
      padding: 14px 16px; /* 押しやすい余白です */
      border: 1px solid var(--line); /* 細い金のわく線です */
      color: var(--muted); /* まだ選んでいないときは弱い色です */
      letter-spacing: 0.08em; /* 長い名前でも収まるよう、字間は控えめです */
      font-size: 0.86rem; /* 4つ並んでも読める大きさです */
      background: rgba(0, 0, 0, 0.22); /* 暗い背景です */
    }}
    /* 選ばれている選択肢の見た目です */
    .channel input:checked + span {{
      border-color: var(--gold); /* わく線をはっきりした金色にします */
      color: #1a140c; /* 文字を濃い色にして読みやすくします */
      background: linear-gradient(180deg, #e0c48a 0%, #c9a56a 48%, #a9844c 100%); /* 金色にします */
      font-weight: 600; /* 少し太くします */
    }}
    /* 「商品説明を作成する」ボタンです */
    button {{
      margin-top: 20px; /* 入力らんとのすき間です */
      width: 100%; /* 横いっぱいにして、しっかり押せるようにします */
      background: linear-gradient(180deg, #e0c48a 0%, #c9a56a 48%, #a9844c 100%); /* 金のグラデーションです */
      color: #1a140c; /* ボタンの文字は濃い茶色にして、読みやすくします */
      border: none; /* わく線は使いません */
      border-radius: 2px; /* 角はほぼ四角で、ビジネスらしい形にします */
      padding: 16px 28px; /* 押しやすい大きさにします */
      font-size: 0.95rem; /* 文字サイズです */
      font-weight: 600; /* 太字にします */
      letter-spacing: 0.22em; /* 字間を広げて、看板のようにします */
      cursor: pointer; /* マウスを指の形にします */
      font-family: inherit; /* 本文と同じ字体です */
    }}
    /* ボタンにマウスを乗せたときの見た目です */
    button:hover {{
      filter: brightness(1.08); /* 少し明るくして「押せる」感じを出します */
    }}
    /* 画面がとても狭いときは、ボタンを1列にします */
    @media (max-width: 520px) {{
      .channel-row {{
        grid-template-columns: 1fr; /* 縦に4つ並べます */
      }}
    }}
    /* 完成原稿カードの本文です */
    .result-body {{
      font-family: "Noto Serif JP", "Segoe UI Emoji", "Apple Color Emoji", serif; /* 完成文は明朝体。絵文字もきれいに出します */
      font-size: 1.02rem; /* 本文サイズです */
      line-height: 2; /* 行間を広めにして、読みやすくします */
      color: #f3ead9; /* やわらかい象牙色の文字です */
    }}
    /* 失敗したときに出す注意の箱です */
    .error {{
      background: rgba(120, 40, 32, 0.28); /* うすい赤黒にします */
      color: #f0c7be; /* 文字は明るい赤みの色です */
      padding: 14px 18px; /* 中の余白です */
      border: 1px solid rgba(240, 180, 170, 0.35); /* 薄い赤のわく線です */
      margin-bottom: 24px; /* 下のカードとのすき間です */
    }}
    /* いちばん下の小さな説明文です */
    .foot {{
      text-align: center; /* 中央揃えにします */
      font-size: 0.78rem; /* 少し小さい文字にします */
      color: var(--muted); /* 薄い色にします */
      letter-spacing: 0.08em; /* 字間です */
    }}
  </style>
</head>
<body>
  <!-- 画面の一番上。タイトルをデカデカと出す場所です -->
  <header class="hero">
    <!-- 個人事業主向けであることを示す、小さな英語ラベルです -->
    <p class="eyebrow">For Sole Proprietors</p>
    <!-- いちばん大きなタイトルです -->
    <h1>AI商品説明<br>作成ツール</h1>
    <!-- タイトルの下の、短い金色の飾り線です -->
    <div class="gold-rule"></div>
    <!-- 何のための道具かを、一言で伝える文です -->
    <p class="hero-sub">1つの画面から、通常・メルカリ・X・Instagram向けの文章を作れます。</p>
  </header>
  <main>
    <!-- 失敗したときだけ、ここに注意メッセージが入ります -->
    {error_box}
    <!-- このフォームは、書いた商品情報を /ask という受付へ送ります -->
    <form class="panel" action="/ask" method="post">
      <!-- カード左上の小さな英語ラベルです -->
      <p class="panel-kicker">Product Brief</p>
      <!-- 入力カードの見出しです -->
      <h2>商品情報</h2>
      <!-- 入力らんの名前（ラベル）です -->
      <label for="message">商品名・素材・特徴・価格・誰向けかを書いてください</label>
      <!-- name="message" が、Python側の message という箱に入ります -->
      <textarea id="message" name="message" required maxlength="2000" placeholder="例: ハンドメイドのレザー名刺入れ / 本革 / 名入れ可 / 8,800円 / 20〜30代のビジネスパーソン向け">{safe_question}</textarea>
      <!-- 出力先を選ぶ説明です。あとからSNSを1つずつ足しやすい形にしています -->
      <label class="field-label">出力の種類</label>
      <!-- 4つの出力先を、格子状にきれいに並べます -->
      <div class="channel-row">
        <!-- いままでの通常の商品説明です -->
        <label class="channel">
          <input type="radio" name="output_type" value="standard" {standard_checked}>
          <span>通常の商品説明</span>
        </label>
        <!-- メルカリ用に出力する選択肢です -->
        <label class="channel">
          <input type="radio" name="output_type" value="mercari" {mercari_checked}>
          <span>メルカリ用に出力</span>
        </label>
        <!-- X（旧Twitter）用に出力する選択肢です -->
        <label class="channel">
          <input type="radio" name="output_type" value="x" {x_checked}>
          <span>X用に出力</span>
        </label>
        <!-- Instagram用に出力する選択肢です -->
        <label class="channel">
          <input type="radio" name="output_type" value="instagram" {instagram_checked}>
          <span>Instagram用に出力</span>
        </label>
      </div>
      <!-- 押すと、上の商品情報と選んだ出力先がサーバーへ送られます -->
      <button type="submit">商品説明を作成する</button>
    </form>
    <!-- AIの商品説明があるときだけ、ここに完成原稿のカードが出ます -->
    {answer_box}
    <!-- 合言葉をコードに書かない、という安全ルールの説明です -->
    <p class="foot">APIキーはコードに書いていません。.env から読み込みます。</p>
  </main>
</body>
</html>"""

# 「/」という住所（さいしょのページ）を開いたときに、この仕事をします
@app.get("/", response_class=HTMLResponse)
# 最初のページを作って返す仕事です
def show_home():
    # まだ商品情報も完成文もない、まっさらなホームページを返します
    return make_html_page()

# 「/ask」という住所に、フォームから商品情報が届いたときに、この仕事をします
@app.post("/ask", response_class=HTMLResponse)
# 画面の入力らん name="message" の中身を、message という箱で受け取ります
def ask_ai(message: str = Form(...), output_type: str = Form("standard")):
    # 入力らんの両はしの空白（スペースや改行）を取り除きます
    question = message.strip()
    # 画面で選ばれた出力先を、小文字の英単語として整えます
    selected_type = (output_type or "standard").strip().lower()
    # 4つのどれでもない値が来たときは、通常モードに戻します
    if selected_type not in CHANNEL_SETTINGS:
        selected_type = "standard"
    # 何も書いていないときは、失敗メッセージつきのページを返して、ここで終わります
    if not question:
        # 空の内容ではAIに聞けないので、画面に理由を出します
        return make_html_page(error_message="商品情報が空です。特徴や価格を書いてから作成してください。", output_type=selected_type)
    # 隠し部屋に合言葉が無いときは、AIに聞けないので、やさしく教えて終わります
    if groq_client is None:
        # 入力内容は残して、.env の作り方を案内します
        return make_html_page(
            # さっき書いた商品情報を、入力らんに残します
            question=question,
            # 合言葉が無い理由を、注意の箱で知らせます
            error_message="まだ .env に GROQ_API_KEY がありません。隠し部屋ファイルを作ってから、もう一度試してください。",
            # 選んでいた出力先も残します
            output_type=selected_type,
        )
    # 選ばれたSNSの設定（追加ルールとお願い文）を取り出します
    channel = CHANNEL_SETTINGS[selected_type]
    # 基本の役割ルールに、そのSNS専用ルールを足します（通常は足しません）
    system_content = SYSTEM_MESSAGE + channel["extra_rules"]
    # 人に渡すお願い文を、選ばれたSNS用にします
    user_intro = channel["user_intro"]
    # ここから先は、本当にAIへ商品情報を送ります。失敗してもアプリが止まらないように try で囲みます
    try:
        # GroqのAIに、「役割の説明」と「商品情報」の2つをセットで渡します
        response = groq_client.chat.completions.create(
            # どのAIを使うかを指定します
            model=GROQ_MODEL,
            # AIに渡す会話のリストです。最初に role: system で役割と絶対ルールを固定します
            messages=[
                # 1つ目: 天才コピーライターとしての役割と、選ばれた出力先の追加ルールです
                {"role": "system", "content": system_content},
                # 2つ目: いま人が書いた商品情報です（これを元に説明文を作ります）
                {"role": "user", "content": f"{user_intro}\n\n{question}"},
            ],
        )
        # AIが返してきた最初の返事の本文だけを取り出します。空なら代わりの文を使います
        answer = response.choices[0].message.content or "商品説明を作れませんでした。"
        # 入力内容と完成した商品説明が入ったホームページを、ブラウザに返します
        return make_html_page(question=question, answer=answer, output_type=selected_type)
    # 合言葉が違う、ネットが切れた、など、何かしらの失敗が起きたときの処理です
    except Exception:
        # アプリを止めずに、画面へやさしい失敗メッセージを出します
        return make_html_page(
            # 失敗しても、書いた商品情報は消さないように残します
            question=question,
            # 内部の詳しいエラーは出さず、次に何をすればよいかだけ伝えます
            error_message="いまAIにうまく届きませんでした。合言葉やネットを確認して、少し待ってからもう一度試してください。",
            # 選んでいた出力先も残します
            output_type=selected_type,
        )

# このファイルを「python main.py」で直接実行したときだけ、下の受付開始が動きます
if __name__ == "__main__":
    # 自分のパソコンの 8000番ドアで、アプリの受付を始めます
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
