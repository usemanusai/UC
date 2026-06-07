1. **Implement `engine/reporting/csv_exporter.py`**
   - Create `SQLiteCSVExporter` class with `export_table_to_csv` static method.
   - Includes error handling and logging.
2. **Add tests for `SQLiteCSVExporter`**
   - Create `engine/reporting/test_csv_exporter.py` and run tests.
3. **Integrate CSV export into `validator_pro_v2.py`**
   - Add a new function `export_db_to_csv()` to handle the logic.
   - Add a new button in `frame_config` (or a similar suitable place) to trigger `export_db_to_csv()`.
   - The function should prompt the user for the db path (defaulting to `output/checked_accounts.db` or `checked_accounts.db`) and then where to save the `.csv` file. It will use the `SQLiteCSVExporter`.
4. **Update `README.md`**
   - Update the features list / results section in `README.md` to mention the "SQLite Log-to-CSV Report Generator".
5. **Add Pre-commit Step**
   - Ensure proper testing, verification, review, and reflection are done by running `pre_commit_instructions`.
6. **Submit**
