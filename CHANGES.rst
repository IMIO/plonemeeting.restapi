Changelog
=========

1.0rc6 (unreleased)
-------------------

- Added `extra_include=pod_templates` for `Meeting` and `MeetingItem`.
  [gbastien]

1.0rc5 (2022-01-03)
-------------------

- When returning annex additional values, ignore `last_updated`.
  [gbastien]

1.0rc4 (2021-11-26)
-------------------

- Default value for parameter `the_objects` changed in
  `ToolPloneMeeting.get_orgs_for_user` (from True to False).
  [gbastien]
- Adapted `utils.may_access_config_endpoints` to only check `tool.isManager`
  if given `cfg` is not None.
  [gbastien]
- Make PMChoiceFieldSerializer use a MissingTerms adapter when value not found
  in vocabulary.
  [gbastien]

1.0rc3 (2021-11-08)
-------------------

- Extended `@users` `plone.restapi` endpoint that by default returns infos for
  a single user or let query several users:

  - `extra_include=groups` will add the organizations the user is member of;

    - in addition, passing `extra_include_groups_suffixes=creators` will add
      the organizations the user is creator for (any suffix may be used);

  - `extra_include=app_groups` will add the user Plone groups;
  - `extra_include=configs` will return the `MeetingConfigs`
    the user has access to;
  - `extra_include=categories`, will return the categories the user is able to
    use for each `MeetingConfig`

    - in addition, `extra_include_categories_config=meeting-config-id` parameter
      will filter results for given `MeetingConfig` id;

  - `extra_include=classifiers`, will return the classifiers the user is able to
    use for each `MeetingConfig`

    - in addition `extra_include_classifiers_config=meeting-config-id` parameter
      will filter results for given `MeetingConfig` ids.

  [gbastien]

- Added `@annex` POST endpoint to be able to add an annex on an existing element.
  [gbastien]
- Changed default behavior of `@get GET` endpoint that will return by default
  the summary version of serialized data, to get the full serialization, then
  parameter `fullobjects` will need to be given.
  [gbastien]
- Serializer may now complete a `@extra_includes` key that list `extra_include`
  values available for it.
  [gbastien]

1.0rc2 (2021-09-28)
-------------------

- Use `Products.PloneMeeting.utils.convert2xhtml` to convert `text/html` data
  to correct format (images to base64 data and xhtml compliant).
  [gbastien]
- Simplify external service call to @item POST (add item):

  - Handle parameter `ignore_not_used_data:true` that will add a warning instead
    raising an error if an optional field is given (in this case, the given
    optional field value is ignored);
  - Handle parameter `ignore_validation_for` that will bypass validation of given
    fields if it is not in data or if it is empty. This makes it possible to add
    an item without every data, the item will have to be completed in the Web UI.

  [gbastien]
- Make sure `externalIdentifier` is always stored as a string, as it may be
  passed in the @add endpoint as an integer, if it is stored as an integer,
  it is not searchable in the `portal_catalog` using the `@search` endpoint
  afterwards.
  [gbastien]
- Fixed `PMLazyCatalogResultSerializer.__call__` to avoid an `UnboundLocalError`
  or duplicates in results when the corresponding object does not exist anymore
  for a brain or when a `KeyError` occured in call to serializer.
  [gbastien]
- Handle anonymization of content.  To do so, added `utils.handle_html` that
  will handle every html data (AT pr DX) and make sure it is compliant with
  what we need:

  - images as base64 data;
  - use `appy.pod` preprocessor to make sure we have valid XHTML;
  - anonymize content if necessary.

  [gbastien]

1.0rc1 (2021-08-17)
-------------------

- Make the summary serializer able to handle `extra_include` and
  `additional_values`. For this, needed to change the way summary serializer is
  handled by `plone.restapi` because by default there is one single summary
  serializer for brain interface but we need to be able to register a summary
  adapter for different interfaces (item, meeting, ...).
  [gbastien]
- Restored `Products.PloneMeeting 4.1.x/4.2.x` backward compatibility.
  [gbastien]
- Defined correct serializers for list fields so we have a `token/value`
  representation in each case (AT/DX for single and multi valued select).
  [gbastien]
- Added some new `extra_include` for `MeetingItem`: `classifier`,
  `groups_in_charge` and `associated_groups`.
  The `extra_include` named `proposingGroup` was renamed to `proposing_group`.
  [gbastien]
- Use `additional_values` in annex serializer to get categorized element infos
  instead yet another parameter `include_categorized_infos`.
  [gbastien]

1.0b2 (2021-07-16)
------------------

- Adapted code and tests now that `Meeting` was moved from `AT` to `DX`.
  [gbastien]
- Manage `extra_include=classifiers` in `@config GET` endpoint.
  [gbastien]
- Do no more require parameter `config_id` when a `type` is given in `@search`
  endpoint.  When `type` is other than `item/meeting`, we simply add it to the
  `query` as `portal_type`.
  `config_id` is only required when `type` is `item` or `meeting`.
  [gbastien]
- Added possibility to filter the `annexes endpoint` on any of the boolean
  attributes (`to_print`, `publishable`, `confidential`, `to_sign/signed`).
  [gbastien]
- Adapted `extra_include=deliberation` that was always returning every variants
  of deliberation (`deliberation/public_deliberation/public_deliberation_decided`),
  now the `extra_include` value is the name of the variants we want to get.
  [gbastien]
- Take into account the `extra_include_fullobjects` in the `MeetingItem` serializer.
  To handle this, it was necessary to implement a summary serializer for `Meeting`.
  [gbastien]
- Added `test_restapi_search_items_extra_include_deliberation_images` showing
  that images are received as base64 data value.
  [gbastien]

1.0b1 (2021-02-03)
------------------

- Override default `PMBrainJSONSummarySerializer` for `ICatalogBrain` from
  `imio.restapi` (that already overrides the one from `plone.restapi`) to
  include metadata `enabled` by default.
  Define also `PMJSONSummarySerializer` for object (not brain) to have a
  summary representation of any objects. This makes it possible to get summary
  serializers for a `MeetingConfig` and it's associated groups while using
  `@config?extra_include=associated_groups`.
  [gbastien]
- Changed behavior of our overrided `@search` : before, it was overriding the
  default `@search` and was requiring a `config_id` to work, now `config_id` is
  optional, when given, it will ease searching for items or meetings, but if
  not given, then the endpoint will have the default `@search` behavior.
  Nevertheless, if parameter `type` is given, then `config_id`
  must be given as well.
  [gbastien]

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
