.PHONY: test test-skills test-setup test-python test-importar-caso

# Run all test suites
test: test-skills test-setup test-python test-importar-caso
	@echo ""
	@echo "All test suites passed."

# Validate all SKILL.md frontmatter against agentskills.io spec
test-skills:
	@echo "=== Validating SKILL.md files ==="
	@python3 tests/validate_skill.py --all

# Test bootstrap script (bash)
test-setup:
	@echo "=== Testing setup.sh ==="
	@bash tests/test_setup.sh

# Run per-skill pytest suites (each skill owns its tests)
test-python:
	@echo "=== Running per-skill Python tests ==="
	@pytest plugin/skills/img2pdf/tests/ \
	        plugin/skills/doc2pdf/tests/ \
	        plugin/skills/pdf-split/tests/ \
	        plugin/skills/juntada/tests/ \
	        -v --tb=short

test-importar-caso:
	@echo "=== Testing importar-caso ==="
	@pytest plugin/skills/importar-caso/tests/ -v --tb=short
