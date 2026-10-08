from scripts.materialize_official_kap_table_cells import parse_event


def test_parse_event_preserves_official_table_cell_matrix():
    raw = b"""
    <html><body>
      <div class="notification-body-scale-123">
        <table class="financial-table dividend-table">
          <tr>
            <td class="taxonomy-field-name-cell">
              <div class="taxonomy-field-name">oda_Currency|</div>
            </td>
            <td class="taxonomy-field-title">
              <div class="content-tr">Para Birimi</div>
            </td>
            <td class="taxonomy-context-value">
              <div class="content-tr">TRY</div>
            </td>
          </tr>
        </table>
      </div>
    </body></html>
    """
    rows = parse_event("123", raw)
    assert any(row["cell_text"] == "Para Birimi" for row in rows)
    assert any(row["cell_text"] == "TRY" for row in rows)
    field_rows = [
        row
        for row in rows
        if row["taxonomy_field_name"] is not None
    ]
    assert field_rows[0]["taxonomy_field_name"] == "oda_Currency|"
    assert field_rows[0]["table_classes"] == "financial-table dividend-table"
