.PHONY: all test codegen verify
all: ; python3 src/run_all.py
codegen: ; cd src && python3 codegen.py
verify: ; cd src && python3 verify_supervisor.py
test: ; cd src && python3 codegen.py >/dev/null && python3 sil.py >/dev/null && python3 sil_tests.py
