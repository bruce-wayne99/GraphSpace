/**
 * Created by adb on 02/11/16.
 */


var apis = {
    notifications: {
        ENDPOINT: '/ajax/notifications/',
        get: function(data, uri, successCallback, errorCallback) {
            url = apis.notifications.ENDPOINT
            if (uri != null) {
                url = url + uri
            }
            apis.jsonRequest('GET', url, data, successCallback, errorCallback)
        },
        update: function(id, data, uri, successCallback, errorCallback) {
            url = apis.notifications.ENDPOINT
            if (uri != null) {
                url = url + uri
            }
            if (id != null) {
                url = url + id
            }
            apis.jsonRequest('PUT', url, data, successCallback, errorCallback)
        },
        read: function(id, data, successCallback, errorCallback) {
            url = apis.notifications.ENDPOINT + 'read/'
            if (id != null) {
                url = url + id
            }
            apis.jsonRequest('PUT', url, data, successCallback, errorCallback)
        }
    },
    jsonRequest: function(method, url, data, successCallback, errorCallback) {
        $.ajax({
            headers: {
                'Accept': 'application/json'
            },
            method: method,
            data: data,
            url: url,
            success: successCallback,
            error: errorCallback
        });
    }

};

var notificationsPage = {
    current_tab_is_unread: true,
    init: function() {
        /**
         * This function is called to setup the notifications page.
         * It will initialize all the event listeners.
         */
        console.log('Loading Notifications Page....');

        $('.owner-mark-all-read').click(function() {
            data = {
                owner_email: $('#UserEmail').val(),
                topic: 'owner'
            }
            apis.notifications.read(
                id = null,
                data = data,
                successCallback = function(response) {
                    // This method is called when notifications are successfully fetched.
                    $('#unread-owner-notification-table').bootstrapTable('refresh')
                    $('#all-owner-notification-table').bootstrapTable('refresh')
                    //$.notify({message: response.message}, {type: 'success'});
                    header.checkNotification()
                },
                errorCallback = function() {
                    // This method is called when  error occurs while updating reads.
                    $.notify({ message: 'Error' }, { type: 'danger' });
                }
            );
        })

        $('#mark-all-read').click(function() {
            data = {
                owner_email: $('#UserEmail').val(),
                topic: 'all'
            }
            apis.notifications.read(
                id = null,
                data = data,
                successCallback = function(response) {
                    // This method is called when notifications are successfully fetched.
                    if (notificationsPage.current_tab_is_unread) {
                        notificationsPage.groupNotificationsTable.notificationsGroupCount(
                            is_read = false,
                            total_val_id = '#unread-group-notification-total',
                            table_div_id = '#unread-group-notification-tables',
                            refresh_tabs = true)
                        $('#unread-owner-notification-table').bootstrapTable('refresh')
                    } else {
                        notificationsPage.groupNotificationsTable.notificationsGroupCount(
                            is_read = null,
                            total_val_id = '#all-group-notification-total',
                            table_div_id = '#all-group-notification-tables',
                            refresh_tabs = true)
                        $('#all-owner-notification-table').bootstrapTable('refresh')
                    }
                    $(".notification-indicator .mail-status.unread").css({ "display": "none" })
                    //$.notify({message: response.message}, {type: 'success'});
                },
                errorCallback = function() {
                    // This method is called when  error occurs while updating reads.
                    $.notify({ message: 'Error' }, { type: 'danger' });
                }
            );
        })

        $('#all-notification').click(function() {
            // Get group notification on click
            notificationsPage.groupNotificationsTable.notificationsGroupCount(
                is_read = null,
                total_val_id = '#all-group-notification-total',
                table_div_id = '#all-group-notification-tables',
                refresh_tabs = true)
            // Get owner notification on click
            $('#all-owner-notification-table').bootstrapTable('refresh')
            notificationsPage.current_tab_is_unread = false

        })

        $('#unread-notification').click(function() {
            notificationsPage.groupNotificationsTable.notificationsGroupCount(
                is_read = false,
                total_val_id = '#unread-group-notification-total',
                table_div_id = '#unread-group-notification-tables',
                refresh_tabs = true)
            $('#unread-owner-notification-table').bootstrapTable('refresh')
            notificationsPage.current_tab_is_unread = true
        })

        $('#send-email-checkbox').change(function() {
            notificationsPage.updateSendEmailStatus()
        });

        notificationsPage.groupNotificationsTable.notificationsGroupCount(
            is_read = false,
            total_val_id = '#unread-group-notification-total',
            table_div_id = '#unread-group-notification-tables',
            refresh_tabs = true)

        notificationsPage.checkSendEmailStatus()

        utils.initializeTabs();
    },
    checkSendEmailStatus: function() {
        apis.notifications.get({
                'owner_email': $('#UserEmail').val()
            },
            uri = "email-status/",
            successCallback = function(response) {
                //params.success(response);
                $('#send-email-checkbox').attr("checked", response.receive_notification_email)
            },
            errorCallback = function() {
                // Fail silently
            }
        );
    },
    updateSendEmailStatus: function() {
        apis.notifications.update(
            id = null,
            data = {
                'owner_email': $('#UserEmail').val()
            },
            uri = "email-status/",
            successCallback = function(response) {
                //params.success(response);
                $('#send-email-checkbox').attr("checked", response.receive_notification_email)
            },
            errorCallback = function() {
                // Fail silently
            }
        );
    },
    notificationsTable: {
        operationsFormatter: function(value, row, index) {
            if (!row.is_read) {
                return [
                    '<a class="mark-as-read" href="javascript:void(0)" title="Mark as read">',
                    '<span class="glyphicon glyphicon-ok mark-as-read-icon" aria-hidden="true"></span>',
                    '</a>'
                ].join('');
            }
            return ''
        },
        createSubNotificationTable: function(ajax, ajaxOptions, columns) {
            $('#sub-notification-modal').modal('toggle')
            var dtable = $('#sub-notification-table-modal')
            dtable.empty()
            var table = $('<table/>')
                .attr('data-toggle', 'table')
                .attr('id', 'sub-notification-table')
                .addClass('table-no-bordered')
                .appendTo(dtable)
            table.bootstrapTable({
                ajax: ajax,
                ajaxOptions: {
                    options: ajaxOptions
                },
                sidePagination: 'server',
                pagination: true,
                dataField: 'notifications',
                sortName: 'created_at',
                sortOrder: 'desc',
                columns: columns
            })
        }
    },
    ownerNotificationsTable: {
        messageFormatter: function(value, row, index) {
            return $('<a>').attr('class', 'click-message').text(row.message)[0].outerHTML;
        },
        markAsRead: function(e, value, row, index) {
            data = {
                owner_email: $('#UserEmail').val(),
                topic: 'owner',
                type: row['type'],
                created_at: row['created_at'],
                first_created_at: row['first_created_at'],
                resource: row['resource']
            }
            apis.notifications.read(
                id = row['is_bulk'] ? null : row['id'],
                data = data,
                successCallback = function(response) {
                    // This method is called when notifications are successfully fetched.
                    //$('#all-owner-notification-table').bootstrapTable('refresh')
                    //$.notify({message: response.message}, {type: 'success'});
                    $('#unread-owner-notification-table').bootstrapTable('remove', {
                        field: 'created_at',
                        values: [row['created_at']]
                    });
                    $("#all-owner-notification-table").bootstrapTable('remove', {
                        field: 'id',
                        values: [row['id']]
                    })
                    row['is_read'] = true
                    $("#all-owner-notification-table").bootstrapTable('insertRow', {
                        index: index,
                        row: row
                    })
                    $("#owner-notification-total").text((parseInt($("#owner-notification-total").text()) - 1));
                },
                errorCallback = function() {
                    // This method is called when  error occurs while updating reads.
                    $.notify({ message: 'Error' }, { type: 'danger' });
                }
            );
        },
        operationEvents: {
            'click .click-message': function(e, value, row, index) {
                // On clicking on the notification
                if (row["is_bulk"]) {
                    if (!row["is_read"]) {
                        notificationsPage.ownerNotificationsTable.markAsRead(e, value, row, index)
                    }
                    notificationsPage.notificationsTable.createSubNotificationTable(notificationsPage.ownerNotificationsTable.getNotifications, {
                        owner_email: $('#UserEmail').val(),
                        topic: 'owner',
                        type: row['type'],
                        created_at: row['created_at'],
                        first_created_at: row['first_created_at'],
                        resource: row['resource'],
                        is_bulk: row['is_bulk'],
                        sub_table: true
                    }, [{
                            field: 'message',
                            title: 'Sub-notifications',
                            valign: 'center',
                            formatter: notificationsPage.ownerNotificationsTable.messageFormatter,
                            events: notificationsPage.ownerNotificationsTable.operationEvents
                        },
                        {
                            field: 'created_at',
                            valign: 'center',
                            //align: 'center',
                            formatter: utils.dateFormatter
                        }
                        /*,
                            {
                                field: 'operations',
                                valign: 'center',
                                align: 'right',
                                formatter: notificationsPage.notificationsTable.operationsFormatter,
                                events: notificationsPage.ownerNotificationsTable.operationEvents
                            }
                        */
                    ])
                } else {
                    window.location.href = '/notification/' + row["id"] + '/redirect/?owner_email=' + $('#UserEmail').val() + '&topic=owner'
                }
            },
            'click .mark-as-read': function(e, value, row, index) {
                // Mark as read
                notificationsPage.ownerNotificationsTable.markAsRead(e, value, row, index)
            }
        },
        unreadNotificationQuery: function() {
            /**
             * This is the custom ajaxOptions function used to load parameters for unread notification ajax request.
             *
             * params - query parameters for the ajax request.
             *          It contains parameters like limit, offset, search.
             */
            return {
                options: {
                    topic: 'owner',
                    tableIdName: '#unread-owner-notification-table',
                    is_read: false
                }
            }
        },
        allNotificationQuery: function(params) {
            /**
             * This is the custom ajaxOptions function used to load parameters for all notification ajax requests.
             *
             * params - query parameters for the ajax request.
             *          It contains parameters like limit, offset, search.
             */
            return {
                options: {
                    topic: 'owner',
                    tableIdName: '#all-owner-notification-table'
                }
            }
        },
        getNotifications: function(params) {
            /**
             * This is the custom ajax request used to load notifications.
             *
             * params - query parameters for the ajax request.
             *          It contains parameters like limit, offset, search.
             */
            $(params.options["tableIdName"]).bootstrapTable('showLoading');
            if (!params.options['sub_table']) {
                $("#owner-notification-total").html('<i class="fa fa-refresh fa-spin fa fa-fw"></i>');
            }
            params.data["owner_email"] = $('#UserEmail').val();
            params.data["topic"] = params.options["topic"]
            params.data["is_read"] = params.options["is_read"]
            params.data["type"] = params.options["type"]
            params.data["created_at"] = params.options["created_at"]
            params.data["first_created_at"] = params.options["first_created_at"]
            params.data["resource"] = params.options["resource"]
            params.data["is_bulk"] = params.options["is_bulk"]

            apis.notifications.get(params.data,
                uri = null,
                successCallback = function(response) {
                    // This method is called when notifications are successfully fetched.
                    $(params.options["tableIdName"]).bootstrapTable('hideLoading');
                    params.success(response);
                    if (!params.options['sub_table']) {
                        $("#owner-notification-total").text(response.total);
                    }
                },
                errorCallback = function() {
                    // This method is called when  error occurs while fetching notifications.
                    params.error('Error');
                }
            );
        }
    },
    groupNotificationsTable: {
        messageFormatter: function(value, row, index) {
            return $('<a>').attr('class', 'click-message').text(row.message)[0].outerHTML;
        },
        markAsRead: function(e, value, row, index) {
            data = {
                owner_email: $('#UserEmail').val(),
                topic: 'group',
                type: row['type'],
                group_id: row['group_id'],
                created_at: row['created_at'],
                first_created_at: row['first_created_at'],
                resource: row['resource']
            }
            apis.notifications.read(
                id = row['is_bulk'] ? null : row['id'],
                data = data,
                successCallback = function(response) {
                    // This method is called when notifications are successfully fetched.
                    notificationsPage.groupNotificationsTable.notificationsGroupCount(
                        is_read = false,
                        total_val_id = '#unread-group-notification-total',
                        table_div_id = '#unread-group-notification-tables',
                        refresh_tabs = false)
                    //$.notify({message: response.message}, {type: 'success'});
                    $('#group-table-false-' + row["group_id"]).bootstrapTable('remove', {
                        field: 'id',
                        values: [row['id']]
                    });
                    $('#group-table-null-' + row["group_id"]).bootstrapTable('remove', {
                        field: 'id',
                        values: [row['id']]
                    })
                    row['is_read'] = true
                    $('#group-table-null-' + row["group_id"]).bootstrapTable('insertRow', {
                        index: index,
                        row: row
                    })
                },
                errorCallback = function() {
                    // This method is called when  error occurs while updating reads.
                    $.notify({ message: 'Error' }, { type: 'danger' });
                }
            );
        },
        operationEvents: {
            'click .click-message': function(e, value, row, index) {
                // On clicking on the notification
                if (row["is_bulk"]) {
                    if (!row["is_read"]) {
                        notificationsPage.groupNotificationsTable.markAsRead(e, value, row, index)
                    }
                    notificationsPage.notificationsTable.createSubNotificationTable(notificationsPage.groupNotificationsTable.getNotifications, {
                        owner_email: $('#UserEmail').val(),
                        topic: 'group',
                        type: row['type'],
                        group_id: row['group_id'],
                        created_at: row['created_at'],
                        first_created_at: row['first_created_at'],
                        resource: row['resource'],
                        is_bulk: row['is_bulk']
                    }, [{
                            field: 'message',
                            title: 'Sub-notifications',
                            valign: 'center',
                            formatter: notificationsPage.groupNotificationsTable.messageFormatter,
                            events: notificationsPage.groupNotificationsTable.operationEvents
                        },
                        {
                            field: 'created_at',
                            valign: 'center',
                            //align: 'center',
                            formatter: utils.dateFormatter
                        }
                        /*,
                        {
                            field: 'operations',
                            valign: 'center',
                            align: 'right',
                            formatter: notificationsPage.notificationsTable.operationsFormatter,
                            events: notificationsPage.groupNotificationsTable.operationEvents
                        }
                        */
                    ])
                } else {
                    window.location.href = '/notification/' + row.id + '/redirect/?owner_email=' + $('#UserEmail').val() + '&topic=group'
                }
            },
            'click .mark-as-read': function(e, value, row, index) {
                // Mark as read
                notificationsPage.groupNotificationsTable.markAsRead(e, value, row, index)
            }
        },
        getNotifications: function(params) {
            /**
             * This is the custom ajax request used to load group notifications.
             *
             * params - query parameters for the ajax request.
             *          It contains parameters like limit, offset, search.
             */

            $(params.options["tableIdName"]).bootstrapTable('showLoading');

            params.data["owner_email"] = $('#UserEmail').val();
            params.data["group_id"] = params.options["group_id"]
            params.data["topic"] = params.options["topic"]
            params.data["is_read"] = params.options["is_read"]
            params.data["type"] = params.options["type"]
            params.data["created_at"] = params.options["created_at"]
            params.data["first_created_at"] = params.options["first_created_at"]
            params.data["resource"] = params.options["resource"]
            params.data["is_bulk"] = params.options["is_bulk"]

            apis.notifications.get(params.data,
                uri = null,
                successCallback = function(response) {
                    // This method is called when notifications are successfully fetched.
                    $(params.options["tableIdName"]).bootstrapTable('hideLoading');
                    params.success(response);
                },
                errorCallback = function() {
                    // This method is called when  error occurs while fetching notifications.
                    params.error('Error');
                }
            );
        },
        notificationsGroupCount: function(is_read, total_val_id, table_div_id, refresh_tabs = true) {
            // Get list of groups in group notification
            data = {
                'member_email': $('#UserEmail').val()
            }
            options = {
                topic: 'group'
            }
            if (is_read != null) {
                data["is_read"] = is_read
                options["is_read"] = is_read
            }
            apis.notifications.get(
                data = data,
                uri = 'group-count',
                successCallback = function(response) {
                    // This method is called when notifications are successfully fetched.
                    var glist = $('ul.group-tabs')
                    var gtable = $(table_div_id)
                    glist.empty()
                    if (refresh_tabs) {
                        gtable.empty()
                    }

                    notificationsPage.notificationsTable.unreadTotal = notificationsPage.notificationsTable.unreadTotal + response.total
                    $(total_val_id).text(response.total);

                    $.each(response.groups, function(i) {
                        var li = $('<li/>')
                            .appendTo(glist)
                        var a = $('<a/>')
                            .attr('href', '#group-table-' + is_read + '-' + response.groups[i]['group']['id'])
                            .text(response.groups[i]['group']['name'])
                            .appendTo(li)
                        var span = $('<span/>')
                            .addClass('badge')
							.addClass('graphspace-notification-badge')
                            .text(response.groups[i]['count'])
                            .appendTo(a)

                        // Refresh the tables in a tab only when complete table update needed
                        if (refresh_tabs) {
                            var table = $('<table/>')
                                .attr('id', 'group-table-' + is_read + '-' + response.groups[i]['group']['id'])
                                .attr('data-toggle', 'table')
                                .addClass('table-no-bordered')
                                .appendTo(gtable)

                            var br = $('<br/>')
                                .appendTo(gtable)

                            options["group_id"] = response.groups[i]['group']['id']
                            options["tableIdName"] = '#group-table-' + response.groups[i]['group']['id']

                            markAllReadTitle = [
                                '<a class="mark-',
                                response.groups[i]['group']['name'],
                                '-',
                                response.groups[i]['group']['id'],
                                '-as-read" title="Mark all as read">',
                                '<span class="glyphicon glyphicon-ok mark-as-read-icon" aria-hidden="true"></span>',
                                '</a>'
                            ]

                            table.bootstrapTable({
                                ajax: notificationsPage.groupNotificationsTable.getNotifications,
                                ajaxOptions: {
                                    options: options
                                },
                                sidePagination: 'server',
                                pagination: true,
                                dataField: 'notifications',
                                sortName: 'created_at',
                                sortOrder: 'desc',
                                columns: [{
                                        field: 'message',
                                        title: response.groups[i]['group']['name'],
                                        valign: 'center',
                                        formatter: notificationsPage.groupNotificationsTable.messageFormatter,
                                        events: notificationsPage.groupNotificationsTable.operationEvents,
										width: '75%'
                                    },
									/*
                                    {
                                        field: 'owner_email',
                                        align: 'right',
                                        valign: 'center',
                                    },
									*/
                                    {
                                        field: 'created_at',
                                        valign: 'center',
                                        align: 'left',
                                        formatter: utils.dateFormatter,
										width: '20%'
                                    },
                                    {
                                        field: 'operations',
                                        title: markAllReadTitle.join(''),
                                        valign: 'center',
                                        align: 'right',
                                        formatter: notificationsPage.notificationsTable.operationsFormatter,
                                        events: notificationsPage.groupNotificationsTable.operationEvents,
										width: '5%'
                                    }
                                ]
                            })

                            // Handling click event for Mark as read for specific groups
                            $('.mark-' + response.groups[i]['group']['name'] + '-' + response.groups[i]['group']['id'] + '-as-read').click(function() {
                                data = {
                                    owner_email: $('#UserEmail').val(),
                                    topic: 'group',
                                    group_id: response.groups[i]['group']['id']
                                }
                                apis.notifications.read(
                                    id = null,
                                    data = data,
                                    apis.notifications.read(
                                        id = null,
                                        data = data,
                                        successCallback = function(response) {
                                            // This method is called when notifications are successfully fetched.
                                            notificationsPage.groupNotificationsTable.notificationsGroupCount(
                                                is_read = false,
                                                total_val_id = '#unread-group-notification-total',
                                                table_div_id = '#unread-group-notification-tables',
                                                refresh_tabs = true)
                                            header.checkNotification()
                                            //$.notify({message: response.message}, {type: 'success'});
                                        },
                                        errorCallback = function() {
                                            // This method is called when  error occurs while updating reads.
                                            $.notify({ message: 'Error' }, { type: 'danger' });
                                        }
                                    )
                                );
                            })
                        }
                    })
                },
                errorCallback = function() {
                    // This method is called when  error occurs while updating reads.
                    $.notify({ message: 'Error' }, { type: 'danger' });
                }
            );
        }
    }
};