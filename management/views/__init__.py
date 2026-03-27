from .legacy import *  # noqa: F401,F403
from .dashboard import dashboard, events_hub, gallery_hub
from cloudinary.uploader import destroy
from .gallery import (
	gallery_albums_list,
	management_album_detail,
	edit_gallery_album,
	deactivate_gallery_album,
	activate_gallery_album,
	delete_gallery_album,
)
from .events import (
	events_list,
	events_admin_list,
	create_event_view,
	edit_event_view,
	deactivate_event,
	activate_event,
	archive_event,
	unarchive_event,
)
