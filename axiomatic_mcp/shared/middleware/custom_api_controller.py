from moesifapi.controllers.api_controller import ApiController
from moesifapi.controllers.base_controller import APIHelper, Configuration, HttpContext


class CustomApiController(ApiController):
    """
    Adds a custom action method to the moesif api client
    """

    def create_action(self, body: dict):
        _query_builder = Configuration.BASE_URI
        _query_builder += "/v1/actions"
        _query_url = APIHelper.clean_url(_query_builder)

        _headers = {
            "content-type": "application/json; charset=utf-8",
            "X-Moesif-Application-Id": Configuration.application_id,
            "User-Agent": Configuration.version,
        }

        _body, _headers = self.generate_post_payload(body, _headers)
        _request = self.http_client.post(_query_url, headers=_headers, parameters=_body)
        _response = self.http_client.execute_as_string(_request)
        _context = HttpContext(_request, _response)

        self.validate_response(_context)

        return _response.headers
