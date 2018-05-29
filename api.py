from aiohttp import web
import json
import asyncio
import asyncpg
import uuid

host_name = 'localhost'
db_name = 'postgres'
user_name = 'postgres'
pwd = '123'


async def new_user(request):
    global conn
    try:
        data = await request.post()
        email = str(data.get('email'))
        first_name = str(data.get('first_name'))
        last_name = str(data.get('last_name'))
        ud = str(uuid.uuid4())
        res = {'result': 'user_id=' + ud}
        await conn.execute('INSERT INTO users VALUES(\''+email+'\',\'' + first_name +'\',\''+str(last_name)+'\',now() ,true,\'' + str(ud)+'\')')
    except Exception as e:
        res = {'result': 'error', 'description': str(e)}
    return web.Response(text=json.dumps(res), status=200)

async def user(request):
    global conn
    try:
        api_key = request.query['api_key']
        try:
            usdel = request.query['delete']
        except:
            usdel = 0
        if usdel == '1': # если ключ к удалению, то обновляем статус
            await conn.execute('UPDATE users SET is_active = False WHERE api_key = \'' + api_key + '\'')
            res = {'result': 'ok'}
        else:
            res = str(dict(await conn.fetchrow('SELECT * FROM users WHERE api_key= \'' + api_key + '\' LIMIT 1')))
    except Exception as e:
        res = {'result': 'error', 'description': str(e)}
    return web.Response(text=json.dumps(res), status=200)

async def albums(request):
    global conn
    try:
        method = str(request.query['method'])
        try:
            id = str(request.query['id'])
        except:
            valid = True
        try:
            name = str(request.query['name'])
        except:
            valid = True
        try:
            user_id = str(request.query['user_id'])
        except:
            valid = True
        try:
            metadata = str(request.query['metadata'])
        except:
            valid = True
        try:
            valid = json_valid(metadata) # проверка metadata
        except:
            valid = True

        if valid:
            res = {'result': 'ok'}
        else:
            res = {'result': 'metadata validation error'}
        if method == 'create' and valid:
            res = await conn.fetchrow('INSERT INTO albums VALUES(DEFAULT,\'' + name + '\',\'' + user_id + '\',\'' + metadata + '\',now(), now ()) RETURNING id')
            res = {'result': 'album_id = ' + str(dict(res))}
        if method == 'read':
            res = str(dict(await conn.fetchrow('SELECT * from albums WHERE id = '+id)))
        if method == 'update' and valid:
            await conn.execute('UPDATE albums SET name = \'' + name + '\', metadata = \'' + metadata + '\', updated = now () WHERE id = ' + id)
        if method == 'delete':
            await conn.execute('DELETE FROM albums  WHERE id = ' + id + '; DELETE FROM tracks WHERE album_id = ' + id)
    except Exception as e:
        res = {'result': 'error', 'description': str(e)}
    return web.Response(text=json.dumps(res), status=200)

async def tracks(request):
    global conn
    try:
        method = str(request.query['method'])
        try:
            id = str(request.query['id'])
        except:
            id = ""
        try:
            name = str(request.query['name'])
        except:
            name = ""
        try:
            album_id = str(request.query['album_id'])
        except:
            album_id = ""
        try:
            created = str(request.query['created'])
        except:
            created = ""
        try:
            user_id = str(request.query['api_key'])
        except:
            user_id = ""
        res = {'result': 'ok'}
        if method == 'create':
            res = await conn.fetchrow('INSERT INTO tracks VALUES(DEFAULT, \'' + name + '\', \'' + album_id + '\',now(), now()) RETURNING id')
            res = {'result': 'track_id = ' + str(dict(res))}
        if method == 'read':
            res = str(dict(await conn.fetchrow('SELECT * FROM tracks WHERE id = ' + id)))
        if method == 'update':
            await conn.execute('UPDATE tracks SET name = \'' + name + '\', album_id = \'' + album_id + '\', updated = now() WHERE  id = ' + id)
        if method == 'delete':
            await conn.execute('DELETE FROM tracks WHERE id = \'' + str(id) + '\'')
    except Exception as e:
        res = {'result': 'error', 'description': str(e)}
    return web.Response(text=json.dumps(res), status=200)

async def make_db_connection():
    global user_name, db_name, host_name
    conn = await asyncpg.connect(user=user_name, password=pwd, database=db_name, host=host_name, command_timeout=60)
    return conn

def json_valid(json_text):
    try:
        json_data = json.loads(json_text)
        # release_year = json_data['release_year']
        # awards = json_data['awards'][0]
        # publisher = json_data['awards']['publisher']
        return True
    except ValueError as e:
        return False


expl = web.Application()
conn = asyncio.get_event_loop().run_until_complete(make_db_connection())

expl.router.add_post('/user', new_user)
expl.router.add_get('/user', user)
expl.router.add_get('/albums', albums)
expl.router.add_get('/tracks', tracks)

web.run_app(expl)
