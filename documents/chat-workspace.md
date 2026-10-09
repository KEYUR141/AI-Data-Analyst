# Chat workspace

The landing page is a blank new-chat screen. Left navigation lists session-owned conversation threads. Select or upload a dataset in the composer and send a question to create a new independent thread. Existing threads have URLs under `/threads/<uuid>/` and preserve their selected dataset.

The middle panel displays saved messages and asynchronous responses. The right canvas starts hidden; selecting 'View results & chart' opens computed tables/charts, while 'View dataset' opens source preview rows. Closing the canvas returns to the chat layout. Mobile navigation uses a toggle; the canvas becomes an overlay on smaller screens.

`workspace_views.py` loads thread history and checks ownership. The planning endpoint accepts a conversation_id and verifies it belongs to the current session and selected dataset. The existing dataset endpoints remain available. No migrations are required for this layout.

The interface is an analyst chat: a dataset is required before the first message. General conversation without data is not implemented. Display restores the latest 50 analysis turns; older history remains stored. Existing default dataset conversations appear in the sidebar too.

Verification: 83 tests pass, including separate threads for the same dataset, cross-session denial, and new-chat landing behavior. Browser visual verification remains pending. Charts and tables are populated from the same stored analysis results, not additional Gemini calls.
