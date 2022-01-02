PYTHON_FILES= */*.py */*/*.py

# Python Code Style
reformat:
	isort ${PYTHON_FILES}
	black ${PYTHON_FILES}
stylecheck:
	isort --check ${PYTHON_FILES}
	black --check ${PYTHON_FILES}
