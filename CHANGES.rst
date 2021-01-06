Changelog
=========

1.0a7 (unreleased)
------------------

- Nothing changed yet.


1.0a6 (2021-01-06)
------------------

- `Products.PloneMeeting.utils.fplog` was moved to
  `imio.helpers.security.fplog`, adapted code accordingly.
  [gbastien]

1.0a5 (2020-12-07)
------------------

- Added parameters `extra_include_proposing_groups`,
  `extra_include_groups_in_charge` and `extra_include_associated_groups`
  to `@config GET` endpoint.
  [gbastien]
- By default, restrict access to endpoints to role `Member`,
  was given to role `Anonymous` by default by `plone.restapi`.
  [gbastien]

1.0a4 (2020-10-14)
------------------

- Completed test showing that `MeetingItem.adviceIndex` was not correctly
  initialized upon item creation.
  [gbastien]
- Added parameter `extra_include_meeting` to `IMeetingItem` serializer.
  [gbastien]
- Completed `IMeeting` serializer `_additional_values` with `formatted_date`,
  `formatted_date_short` and `formatted_date_long`.
  [gbastien]

1.0a3 (2020-09-10)
------------------

- Fixed `test_restapi_config_extra_include_categories` as former
  `AT MeetingCategory` are now `DX meetingcategory` that use field `enabled`
  instead workflow `review_state` `active`.
  [gbastien]
- Added `test_restapi_add_item_wf_transitions` that was broken
  with `imio.restapi<1.0a11`.
  [gbastien]
- When adding a new item, insert the event `create_element_using_ws_rest`
  in the `workflow_history` at the beginning, just after the `created` event.
  [gbastien]

1.0a2 (2020-06-24)
------------------

- Added test `test_restapi_annex_type_only_for_meeting_managers`, make sure an
  annex `content_category` that is restricted to `MeetingManagers` using
  `content_category.only_for_meeting_managers` is rendered the same way.
  [gbastien]
- Try to build a more easy api :

  - Turned `@search_items` into `@search` and `@search_meetings` into
    `@search?type=meeting`;
  - Parameter `getConfigId` is renamed to `config_id`;
  - Added `in_name_of` parameter making it possible to use endpoint as another
    user if original user is `(Meeting)Manager`.

  [gbastien]
- Added `@item` POST endpoint to be able to create item with/without annexes:

  - Need to define new AT fields `deserializer` to apply WF before settings
    field values;
  - Manage optional fields (can not use when not enabled);
  - Manage creation of annexes as `__children__` of item;
  - Ease use by being able to define `config_id` only at first level
    (so not for annexes);
  - Ease use by being able to use organizations `ids` instead `UIDs`
    in creation data;
  - Manage `in_name_of` parameter.

  [gbastien]
- Override `@infos` endpoint from imio.restapi to add our own informations.
  [gbastien]
- Added parameter `meetings_accepting_items=True` to `@search`
  when `type=meeting`, this will query only meetings accepting items but query
  may still be completed with other arbitrary indexes.
  [gbastien]
- Added `@config` endpoint that will return a given `config_id` `MeetingConfig`
  informations. Parameters `include_categories` (return enabled/disabled
  categories), `include_pod_templates` (return enabled POD template) and
  `include_searches` (return enabled DashboardCollections) are available.
  [gbastien]
- Added `@get` endpoint that receives an `UID` and returns the object found.
  A convenience endpoint `@item` do the same but just check that returned element
  is a MeetingItem.
  [gbastien]
- Added parameter `base_search_uid=collection_uid` to `@search`,
  this makes it possible to use the `query` defined on a `DashboardCollection`.
  [gbastien]

1.0a1 (2020-01-10)
------------------

- Initial release.
  [gbastien]
