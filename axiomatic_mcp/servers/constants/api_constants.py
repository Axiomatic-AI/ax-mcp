from urllib.parse import quote


class ApiRoutes:
    # NOTE: When adding a new endpoint, make sure the router in the API uses the is_external_user_guard.
    GET_SAX_SPECTRUM = "/pic/circuit/get_sax_spectrum"
    REFINE_CIRCUIT = "/pic/circuit/refine"
    FORMALIZE_CIRCUIT = "/pic/circuit/formalize"
    SUBMIT_USER_FEEDBACK = "/pic/user-feedback"
    GET_CURRENT_USER = "/users/me"
    GET_OPTIMIZABLE_PARAMETERS = "/pic/circuit/optimizable-parameters"
    GET_OPTIMIZED_CODE = "/pic/circuit/code/optimizations"
    VALIDATE_STATEMENTS = "/pic/circuit/statements/validation"
    # Matches FORMALIZE_CIRCUIT, but different intent
    FORMALIZE_STATEMENT = "/pic/circuit/formalize"
    INFORMALIZE_STATEMENT = "/pic/circuit/statement/informalize"
    PDK_LIST = "/pic/pdks"
    PDK_PERMISSION = "/users/pdk-permissions/me"

    @staticmethod
    def pdk_info(pdk_type: str) -> str:
        """
        Build endpoint for PDK info.
        Encodes the pdk_type safely for URLs.
        """
        return f"/pic/pdk/{quote(pdk_type)}/info"
