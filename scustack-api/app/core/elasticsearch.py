from app.core.config import settings

try:
    from elasticsearch import AsyncElasticsearch
    es = AsyncElasticsearch(settings.ES_HOST)
except ImportError:
    es = None

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
                'fields': {
                    'raw': {'type': 'keyword'},
                    'suggest': {'type': 'completion'},
                },
            },
            'description': {
                'type': 'text',
                'analyzer': 'ik_max_word_analyzer',
                'search_analyzer': 'ik_smart_analyzer',
            },
            'content_text': {
                'type': 'text',
                'analyzer': 'ik_max_word_analyzer',
                'search_analyzer': 'ik_smart_analyzer',
            },
            'course_name': {
                'type': 'text',
                'analyzer': 'ik_max_word_analyzer',
                'search_analyzer': 'ik_smart_analyzer',
                'fields': {
                    'raw': {'type': 'keyword'},
                    'suggest': {'type': 'completion'},
                },
            },
            'course_aliases': {'type': 'keyword'},
            'college_name': {
                'type': 'text',
                'fields': {'raw': {'type': 'keyword'}},
            },
            'course_id': {'type': 'keyword'},
            'college_id': {'type': 'keyword'},
            'semester': {'type': 'keyword'},
            'category': {'type': 'keyword'},
            'format': {'type': 'keyword'},
            'source_type': {'type': 'keyword'},
            'trust_status': {'type': 'keyword'},
            'review_status': {'type': 'keyword'},
            'contributor_id': {'type': 'keyword'},
            'thumbnail_version_id': {'type': 'keyword'},
            'created_at': {'type': 'date'},
            'updated_at': {'type': 'date'},
            'download_count': {'type': 'long'},
            'rating_avg': {'type': 'float'},
            'rating_count': {'type': 'integer'},
        }
    },
}


async def ensure_materials_index() -> None:
    if es is None:
        return
    exists = await es.indices.exists(index=MATERIALS_INDEX)
    if not exists:
        await es.indices.create(index=MATERIALS_INDEX, body=MATERIALS_MAPPING)


async def index_material(material_id: str, document: dict) -> None:
    if es is None:
        return
    await es.index(index=MATERIALS_INDEX, id=material_id, body=document, refresh=True)


async def update_material_fields(material_id: str, fields: dict) -> None:
    if es is None:
        return
    await es.update(index=MATERIALS_INDEX, id=material_id, doc=fields, refresh=True)


async def delete_material_index(material_id: str) -> None:
    if es is None:
        return
    await es.delete(index=MATERIALS_INDEX, id=material_id, ignore=[404])


def _es_guard():
    if es is None:
        raise RuntimeError('elasticsearch not installed')


async def search_materials(
    query: str,
    filters: dict | None = None,
    sort: str = 'relevance',
    page: int = 1,
    page_size: int = 20,
) -> dict:
    must = []
    if query:
        must.append({
            'multi_match': {
                'query': query,
                'fields': ['title^3', 'description^2', 'content_text^2', 'course_name^2', 'course_aliases^2'],
                'type': 'best_fields',
            }
        })

    sort_body = _build_sort(sort)
    search_body = {
        'query': {
            'function_score': {
                'query': {'bool': {'must': must, 'filter': _build_filters(filters)}},
                'functions': [
                    {
                        'filter': {'term': {'trust_status': 'maintainer_picked'}},
                        'weight': 3,
                    },
                    {
                        'filter': {'term': {'trust_status': 'community_verified'}},
                        'weight': 2,
                    },
                    {
                        'field_value_factor': {
                            'field': 'rating_avg',
                            'factor': 1.5,
                            'missing': 0,
                        },
                    },
                    {
                        'field_value_factor': {
                            'field': 'download_count',
                            'factor': 0.001,
                            'modifier': 'log1p',
                            'missing': 0,
                        },
                    },
                ],
                'boost_mode': 'multiply',
                'score_mode': 'sum',
            }
        },
        'from': (page - 1) * page_size,
        'size': page_size,
        'sort': sort_body,
    }
    return await es.search(index=MATERIALS_INDEX, body=search_body)


async def suggest(query: str, size: int = 8) -> dict:
    body = {
        'suggest': {
            'course_suggest': {
                'prefix': query,
                'completion': {
                    'field': 'course_name.suggest',
                    'size': size // 2,
                    'skip_duplicates': True,
                },
            },
            'title_suggest': {
                'prefix': query,
                'completion': {
                    'field': 'title.suggest',
                    'size': size // 2,
                    'skip_duplicates': True,
                },
            },
        },
    }
    return await es.search(index=MATERIALS_INDEX, body=body)


def _build_sort(sort: str) -> list:
    if sort == 'newest':
        return [{'created_at': {'order': 'desc'}}]
    if sort == 'downloads':
        return [{'download_count': {'order': 'desc'}}]
    if sort == 'rating':
        return [{'rating_avg': {'order': 'desc'}}]
    return [{'_score': {'order': 'desc'}}, {'created_at': {'order': 'desc'}}]


def _build_filters(filters: dict | None) -> list:
    if not filters:
        return []
    result = []
    for field, value in filters.items():
        if value is not None:
            result.append({'term': {field: value}})
    return result
