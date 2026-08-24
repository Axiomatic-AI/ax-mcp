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
    PDK_INFO = "/pic/pdk/{pdk_type}/info"
    MCP_MODEL_FEEDBACK = "/mcp/model-feedback"
    ARGMIN_WRITE_CODE = "/numerics/argmin/write-code"
    ARGMIN_EXECUTE = "/numerics/argmin/execute"
    MODEL_FITTER_WRITE_CODE = "/numerics/model-fitter/write-code"
    MODEL_FITTER_EXECUTE = "/numerics/model-fitter/execute"
    EQUATIONS_DERIVE = "/expressions/derive"
    EQUATIONS_CHECK = "/expressions/check"
    # NOTE: these paths are set by the backend and shared publicly via this repo — do not
    # introduce new path segments here that name a specific vendor/technology (e.g. a DB engine).
    KNOWLEDGE_BASE_SEARCH = "/neo4j/search"
    KNOWLEDGE_BASE_GET_SCHEMA = "/neo4j/get-schema"
    KNOWLEDGE_BASE_OVERVIEW = "/neo4j/overview"
    KNOWLEDGE_BASE_LIST_PAPERS = "/neo4j/papers"
    ARXIV_SEARCH_WORKS = "/search/arxiv/works"
    OPENALEX_SEARCH_WORKS = "/search/openalex/works"
    TIDY3D_GENERATE_CODE = "/tidy3d/generate-code"
    TIDY3D_EXECUTE_CODE = "/tidy3d/execute-code"
    TIDY3D_START_TASK = "/tidy3d/start-task"
    TIDY3D_TASK_STATUS = "/tidy3d/task-status"
    # The three meep execute routes are gated by is_playground_user_guard
    # (ADMIN/INTERNAL/PLAYGROUND), not is_external_user_guard: every submission spins up a
    # Kubernetes pod with conda + MPI. Same gating as ARGMIN_EXECUTE and TIDY3D_EXECUTE_CODE.
    MEEP_WRITE_CODE = "/numerics/meep/write-code"
    MEEP_EXECUTE = "/numerics/meep/execute"
    MEEP_EXECUTE_STATUS = "/numerics/meep/execute/status/{task_id}"
    MEEP_EXECUTE_RESULTS = "/numerics/meep/execute/results/{task_id}"
