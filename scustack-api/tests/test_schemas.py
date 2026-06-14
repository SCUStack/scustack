from uuid import uuid4

from app.schemas.common import ApiResponse, ErrorCode, PaginatedData
from app.schemas.user import UserResponse


class TestApiResponse:
    def test_success_response(self):
        resp = ApiResponse(data={'key': 'value'})
        assert resp.code == 0
        assert resp.message == 'ok'
        assert resp.data == {'key': 'value'}

    def test_defaults(self):
        resp = ApiResponse()
        assert resp.code == 0
        assert resp.data is None
        assert resp.message == 'ok'


class TestErrorCode:
    def test_error_codes(self):
        assert ErrorCode.SUCCESS == 0
        assert ErrorCode.NOT_FOUND == 40400
        assert ErrorCode.INTERNAL_ERROR == 50000


class TestUserResponse:
    def test_from_attributes(self):
        user_id = uuid4()
        user = UserResponse.model_validate({
            'id': str(user_id),
            'nickname': '测试用户',
            'avatar_url': None,
            'role': 'student',
        })
        assert user.nickname == '测试用户'
        assert user.role == 'student'
        assert user.id == user_id
