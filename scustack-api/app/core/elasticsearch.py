from elasticsearch import AsyncElasticsearch

from app.core.config import settings

es = AsyncElasticsearch(settings.ES_HOST)


MATERIALS_INDEX = 'materials'

MATERIALS_MAPPING = {
    'settings': {
        'analysis': {
            'analyzer': {
                'ik_smart_analyzer': {
                    'type': 'custom',
                    'tokenizer': 'ik_smart',
                    'filter': ['lowercase'],
                },
                'ik_max_word_analyzer': {
                    'type': 'custom',
                    'tokenizer': 'ik_max_word',
                    'filter': ['lowercase'],
                },
            },
        },
    },
    'mappings': {
        'properties': {
            'title': {
                'type': 'text',
                'analyzer': 'ik_max_word_analyzer',
                'search_analyzer': 'ik_smart_analyzer',
                'fields': {'raw': {'type': 'keyword'}},
            },
            'description': {
                'type': 'text',
                'analyzer': 'ik_max_word_analyzer',
                'search_analyzer': 'ik_smart_analyzer',
            },
            'course_name': {
                'type': 'text',
                'analyzer': 'ik_max_word_analyzer',
                'search_analyzer': 'ik_smart_analyzer',
                'fields': {'raw': {'type': 'keyword'}},
            },
            'college_name': {
                'type': 'text',
                'fields': {'raw': {'type': 'keyword'}},
            },
            'semester': {'type': 'keyword'},
            'category': {'type': 'keyword'},
            'format': {'type': 'keyword'},
            'source_type': {'type': 'keyword'},
            'trust_status': {'type': 'keyword'},
            'tags': {'type': 'keyword'},
            'contributor_id': {'type': 'keyword'},
            'created_at': {'type': 'date'},
            'updated_at': {'type': 'date'},
            'download_count': {'type': 'long'},
            'rating_avg': {'type': 'float'},
        }
    },
}


async def ensure_materials_index() -> None:
    exists = await es.indices.exists(index=MATERIALS_INDEX)
    if not exists:
        await es.indices.create(index=MATERIALS_INDEX, body=MATERIALS_MAPPING)


async def index_material(material_id: str, document: dict) -> None:
    await es.index(index=MATERIALS_INDEX, id=material_id, body=document, refresh=True)


async def delete_material_index(material_id: str) -> None:
    await es.delete(index=MATERIALS_INDEX, id=material_id, ignore=[404])


async def search_materials(
    query: str,
    filters: dict | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    must = []
    if query:
        must.append(
            {
                'multi_match': {
                    'query': query,
                    'fields': ['title^3', 'description^2', 'course_name^2', 'tags'],
                }
            }
        )
    search_body = {
        'query': {'bool': {'must': must, 'filter': _build_filters(filters)}},
        'from': (page - 1) * page_size,
        'size': page_size,
        'sort': [{'_score': {'order': 'desc'}}, {'created_at': {'order': 'desc'}}],
    }
    return await es.search(index=MATERIALS_INDEX, body=search_body)


def _build_filters(filters: dict | None) -> list:
    if not filters:
        return []
    result = []
    for field, value in filters.items():
        if value is not None:
            result.append({'term': {field: value}})
    return result
