import requests, os
from lxml import etree


query = '''
query ($username: String, $type: MediaType) {
    MediaListCollection(userName: $username, type: $type) {
        lists {
            name
            entries {
                media {
                    idMal
                    title {
                        english
                        romaji
                        native
                    }
                    format
                    episodes
                    volumes
                    chapters
                }
                progress
                progressVolumes
                startedAt {
                    year
                    month
                    day
                }
                completedAt {
                    year
                    month
                    day
                }
                score(format: POINT_10_DECIMAL)
                repeat
                notes
            }
        }
    }
}
'''

urlAPI = 'https://graphql.anilist.co'


# Parse None based date from the json
def parseDate(date: dict) -> str:
    date_ = ''
    for key, val in date.items():
        if val == None and key == 'year':
            date_ += '0000'
        elif val == None:
            date_ += '00'
        else:
            date_ += f'{str(val):0>2}'
        date_ += '-'

    return date_[:-1]



# Find total count from each category
def userTotal(data: list, status: str) -> int:
    for category in data:
        if category['name'] == status:
            return len(category['entries'])
    return 0



# Fallback if title of specific language not found
def mediaTitle(data: dict, title: str) -> str:
    if data[title]:
        return data[title].replace('>', '').replace('<', '')

    for key, value in data.items():
        if value:
            return value.replace('>', '').replace('<', '')



def xmlParserAnime(animeList, variables, title):
    mediaList = animeList['data']['MediaListCollection']['lists']

    animeXML = f'''<myanimelist>

    <myinfo>
        <user_id>11266165</user_id>
        <user_name>{variables['username']}</user_name>
        <user_export_type>1</user_export_type>
        <user_total_anime>{sum(len(i['entries']) for i in mediaList)}</user_total_anime>
        <user_total_watching>{userTotal(mediaList, 'Watching')}</user_total_watching>
        <user_total_completed>{userTotal(mediaList, 'Completed')}</user_total_completed>
        <user_total_onhold>{userTotal(mediaList, 'Paused')}</user_total_onhold>
        <user_total_dropped>{userTotal(mediaList, 'Dropped')}</user_total_dropped>
        <user_total_plantowatch>{userTotal(mediaList, 'Planning')}</user_total_plantowatch>
    </myinfo>

'''

    format_ = {
        'TV'        : 'TV',
        'MOVIE'     : 'Movie',
        'OVA'       : 'OVA',
        'ONA'       : 'ONA',
        'SPECIAL'   : 'Special',
        'TV_SHORT'  : 'Short',
        'MUSIC'     : 'Music'
    }

    status = {
        'Completed' : 'Completed',
        'Watching'  : 'Watching',
        'Dropped'   : 'Dropped',
        'Paused'    : 'On-Hold',
        'Planning'  : 'Plan to Watch'
    }

    for my_status in mediaList:
        for entry in my_status['entries']:
            if my_status['name'] != 'Favorites':
                field = f'''
    <anime>
        <series_animedb_id>{entry['media']['idMal']}</series_animedb_id>
        <series_title>{mediaTitle(entry['media']['title'], title)}</series_title>
        <series_type>{format_.get(entry['media']['format'], 'TV')}</series_type>
        <series_episodes>{entry['media']['episodes'] if entry['media']['episodes'] else 0}</series_episodes>
        <my_id>0</my_id>
        <my_watched_episodes>{entry['progress']}</my_watched_episodes>
        <my_start_date>{parseDate(entry['startedAt'])}</my_start_date>
        <my_finish_date>{parseDate(entry['completedAt'])}</my_finish_date>
        <my_rated></my_rated>
        <my_score>{entry['score']}</my_score>
        <my_storage></my_storage>
        <my_storage_value>0.00</my_storage_value>
        <my_status>{status.get(my_status['name'], '')}</my_status>
        <my_comments>{entry['notes'] if entry['notes'] else ''}</my_comments>
        <my_times_watched>{entry['repeat']}</my_times_watched>
        <my_rewatch_value></my_rewatch_value>
        <my_priority>LOW</my_priority>
        <my_tags></my_tags>
        <my_rewatching>0</my_rewatching>
        <my_rewatching_ep>0</my_rewatching_ep>
        <my_discuss>0</my_discuss>
        <my_sns>default</my_sns>
        <update_on_import>1</update_on_import>
    </anime>
'''
                animeXML += field

    animeXML += '\n</myanimelist>'
    animeXML = animeXML.replace('&', 'and')

    # Sorting The XML based on Title and Watch status
    tree = etree.ElementTree(etree.fromstring(animeXML))

    for node in tree.xpath('//myanimelist'):
        node[:] = sorted(node, key=lambda ch: (ch.xpath('my_status/text()'), ch.xpath('series_title/text()')))

    return tree



def xmlParserManga(animeList, variables, title):
    mediaList = animeList['data']['MediaListCollection']['lists']

    animeXML = f'''<myanimelist>

    <myinfo>
        <user_id>11266165</user_id>
        <user_name>{variables['username']}</user_name>
        <user_export_type>2</user_export_type>
        <user_total_manga>{sum(len(i['entries']) for i in mediaList)}</user_total_manga>
        <user_total_reading>{userTotal(mediaList, 'Reading')}</user_total_reading>
        <user_total_completed>{userTotal(mediaList, 'Completed')}</user_total_completed>
        <user_total_onhold>{userTotal(mediaList, 'Paused')}</user_total_onhold>
        <user_total_dropped>{userTotal(mediaList, 'Dropped')}</user_total_dropped>
        <user_total_plantoread>{userTotal(mediaList, 'Planning')}</user_total_plantoread>
    </myinfo>

'''

    status = {
        'Completed' : 'Completed',
        'Reading'   : 'Reading',
        'Dropped'   : 'Dropped',
        'Paused'    : 'On-Hold',
        'Planning'  : 'Plan to Read'
    }

    for my_status in mediaList:
        for entry in my_status['entries']:
            if my_status['name'] != 'Favorites':
                field = f'''
    <manga>
        <manga_mangadb_id>{entry['media']['idMal']}</manga_mangadb_id>
        <manga_title>{mediaTitle(entry['media']['title'], title)}</manga_title>
        <manga_volumes>{entry['media']['volumes'] if entry['media']['volumes'] else 0}</manga_volumes>
        <manga_chapters>{entry['media']['chapters'] if entry['media']['chapters'] else 0}</manga_chapters>
        <my_id>0</my_id>
        <my_read_volumes>{entry['progressVolumes']}</my_read_volumes>
        <my_read_chapters>{entry['progress']}</my_read_chapters>
        <my_start_date>{parseDate(entry['startedAt'])}</my_start_date>
        <my_finish_date>{parseDate(entry['completedAt'])}</my_finish_date>
        <my_scanalation_group></my_scanalation_group>
        <my_score>{entry['score']}</my_score>
        <my_storage></my_storage>
        <my_retail_volumes>0</my_retail_volumes>
        <my_status>{status.get(my_status['name'], 'Completed')}</my_status>
        <my_comments>{entry['notes'] if entry['notes'] else ''}</my_comments>
        <my_times_read>{entry['repeat']}</my_times_read>
        <my_tags></my_tags>
        <my_priority>Low</my_priority>
        <my_reread_value/>
        <my_rereading>NO</my_rereading>
        <my_discuss>YES</my_discuss>
        <my_sns>default</my_sns>
        <update_on_import>1</update_on_import>
    </manga>
'''
                animeXML += field

    animeXML += '\n</myanimelist>'
    animeXML = animeXML.replace('&', 'and')

    # Sorting The XML based on Title and Watch status
    tree = etree.ElementTree(etree.fromstring(animeXML))

    for node in tree.xpath('//myanimelist'):
        node[:] = sorted(node, key=lambda ch: (ch.xpath('my_status/text()'), ch.xpath('manga_title/text()')))

    return tree



def fileParser(username: str, type_ = 'ANIME', title = 'english') -> str:
    variables = {
        'username': username,
        'type': type_
    }

    response = requests.post(urlAPI, json={'query': query, 'variables': variables})
    animeList = response.json()

    if 'errors' in animeList:
        error = animeList['errors'][0]['message']
        if 'User' in error:
            return error + '\nCheck username again!!!'
        else:
            return error + '\nEnter proper MediaType (ANIME | MANGA)!!!'

    if variables['type'] == 'ANIME':
        tree = xmlParserAnime(animeList=animeList, variables=variables, title=title)
    else:
        tree = xmlParserManga(animeList=animeList, variables=variables, title=title)


    # Export XML file
    path = os.path.join(os.path.dirname(__file__), f"MAL-{variables['username']}-{variables['type']}.xml")

    tree.write(path, encoding='utf-8')

    return path