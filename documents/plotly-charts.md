# Plotly charts

DuckDB results feed `services/charts.py`. The backend checks unique axis names, nonmissing points, finite numeric values, scatter axis types, line ordering, and pie values before creating a Plotly figure. Truncated result sets are not charted to avoid misleading totals. Invalid chart requests add a note while retaining calculated tables.

Bar, line, pie, and scatter are supported. Line points are ordered by numeric x or ISO date. Missing axis values are omitted. Chart labels are HTML-escaped. Figures are returned as JSON and rendered using `Plotly.newPlot`; raw provider HTML is never inserted.

The Plotly.js bundle is served locally from `Project/static/vendor/plotly.min.js`, generated from the installed Python package using `plotly.offline.get_plotlyjs()`. Its embedded license notice is retained. If upgrading Plotly, regenerate the bundle to match. No chart data is sent to a hosted Plotly service.

The browser enables hover, zoom, and PNG downloads, with responsive sizing. Results remain available as a table if rendering fails. Browser visual verification is still required.

Try: 'Show revenue by region as a bar chart', 'Show monthly revenue as a line chart', 'Show revenue share by product as a pie chart', or 'Plot quantity against revenue as a scatter chart'. The planner must request a chart for one to appear.
