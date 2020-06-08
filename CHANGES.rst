Changelog
=========

1.0a2 (unreleased)
------------------

- Added test `test_restapi_annex_type_only_for_meeting_managers`, make sure an
  annex `content_category` that is restricted to `MeetingManagers` using
  `content_category.only_for_meeting_managers` is rendered the same way.
  [gbastien]
- Try to build a more easy api :

  - Turned `@search_items` into `@search` and `@search_meetings` into `@search?type=meeting`;
  - Parameter `getConfigId` is renamed to `config_id`.
  [gbastien]
- Added `@item` POST endpoint to be able to create item with or without annexes :

  - Need to define new AT fields `deserializer` to apply WF before settings field values;
  - Manage optional fields (can not use when not enabled);
  - Manage creation of annexes as `__children__` of item;
  - Ease use by being able to define `config_id` only at first level (so not for annexes);
  - Ease use by being able to use organizations `ids` instead `UIDs` in creation data.
  [gbastien]
- Added `@wf-infos` endpoint that will return informations about `WS versions`
  and `currently connected user`.
  [gbastien]

1.0a1 (2020-01-10)
------------------

- Initial release.
  [gbastien]
