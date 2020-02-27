import aiohttp
import asyncio

import uvicorn
from fastai.vision import *
from torchvision import transforms
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse, StreamingResponse
from starlette.staticfiles import StaticFiles
from app.heatmap import scale_down



class Aprendizaje():
    "Structure  to  save learner name and descriptión"
    def __init__(self, learner: Learner, name: str, description: str):
        self.learner = learner
        self.nombre = name
        self.description = description


csv.register_dialect('no_quotes', delimiter=',',
                     quoting=csv.QUOTE_ALL, skipinitialspace=True)
csv_file_url = ('https://drive.google.com/uc?export=download&id='
                '1XnsR_yHikArrY3aZzlylH02jhqIQ9-kR')
csv_file_name = 'parametros.csv'
path = Path(__file__).parent / 'app'
path_model = path / 'models'
path_img = path / 'static'
global_img : Image
global_learner: Aprendizaje

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))
#app.mount('/static', StaticFiles(directory='static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner():
    global global_learner
    await download_file(csv_file_url, path_model / csv_file_name)
    with open(path_model / csv_file_name, 'r') as description:
        reader = csv.reader(description, dialect='no_quotes')
        red = reader.__next__()
    learner_name, learner_desription, onedrive_url=red
    await download_file(onedrive_url, path_model / learner_name)
    try:
        global_learner=Aprendizaje (load_learner(path_model, learner_name),
                                        learner_name, learner_desription)
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise
    return


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    global global_img
    img_data = await request.form()
    img_bytes = await (img_data['file'].read())
    img_pil = PIL.Image.open(BytesIO(img_bytes))
    global_img = scale_down(img_pil, 1024)
    mask, msk_tensor, dummy = global_learner.learner.predict(global_img)
    msk_np = image2np(msk_tensor)
    msk_pil = PIL.Image.frombytes("L", msk_np.shape, (msk_np * 255).astype(np.uint8))
    msk_pil = msk_pil.resize((img_pil.size[0], img_pil.size[1]), resample=PIL.Image.BILINEAR)
    if img_pil.mode in ['P', 'RGBA']:
        img_pil = img_pil.convert('L')
    elif img_pil.mode != msk_pil.mode:
        msk_pil = msk_pil.convert(img_pil.mode)
    blend = PIL.Image.blend(img_pil, msk_pil, 0.35)
    with io.BytesIO() as contenido:
        blend.save(contenido, format('JPEG'))
        crudo = contenido.getvalue()
    return StreamingResponse(BytesIO(crudo), media_type='image/jpeg')


if __name__ == '__main__':
    if 'serve' in sys.argv:
        puerto = int(sys.argv[2])
        uvicorn.run(app=app, host='0.0.0.0', port=puerto, log_level="info")
    elif 'load' not in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")

