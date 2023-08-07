//Include C header files
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


#include "nvs_flash.h"

#include "esp_err.h"
#include "esp_log.h"

#include "esp_bt.h"
#include "esp_bt_main.h"
#include "esp_gap_ble_api.h"

#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_http_client.h"

#include "Credentials.h"

#define FS_ID 2
#define OFFSET 101

int8_t RSSI[10] = {0};

static void wifi_event_handler(void *event_handler, esp_event_base_t event_base, int32_t wifi_event_id, void *event_data)
{
    switch (wifi_event_id)
    {
    case WIFI_EVENT_STA_START:
        printf("\tConnecting to LAN\n");
        break;
    case WIFI_EVENT_STA_CONNECTED:
        printf("\tConnected to LAN\n");
        break;
    case WIFI_EVENT_STA_DISCONNECTED:
        printf("\tWiFi lost connection\n");
        break;
    case IP_EVENT_STA_GOT_IP:
        printf("\tFixedStation got IP Address\n");
        break;
    default:
        break;
    }
}

void LAN_connection()
{
    // 1 - Wi-Fi/LwIP Init Phase
    ESP_ERROR_CHECK(esp_netif_init());                
    ESP_ERROR_CHECK(esp_event_loop_create_default()); 
    esp_netif_create_default_wifi_sta();              
    wifi_init_config_t wifi_initiation = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&wifi_initiation)); 
    esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_event_handler, NULL);
    esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_event_handler, NULL);
    wifi_config_t wifi_configuration = {
        .sta = {
            .ssid = SSID,
            .password = PASS}};
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    (esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_configuration));
    // 3 - Wi-Fi Start Phase
    ESP_ERROR_CHECK(esp_wifi_start());
    // 4- WiESP_ERROR_CHECK-Fi Connect Phase
    ESP_ERROR_CHECK(esp_wifi_connect());
}

esp_err_t client_event_post_handler(esp_http_client_event_handle_t evt)
{
    switch (evt->event_id)
    {
    case HTTP_EVENT_ON_DATA:
        printf("HTTP_EVENT_ON_DATA: %.*s\n", evt->data_len, (char *)evt->data);
        break;

    default:
        break;
    }
    return ESP_OK;
}

static void post_data(int fs_id, int beacon_id, int RSSI)
{
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_wifi_connect());
    char post_data[500];
    sprintf(post_data, "http://192.168.43.136:5000/PushData?fixed_station_id=%d&beacon_id=%d&RSSI=%d", fs_id, beacon_id, RSSI);
    printf("%s", post_data);

    esp_http_client_config_t config_post = {
        .url = post_data,
        .method = HTTP_METHOD_POST,
        .cert_pem = NULL,
        .event_handler = client_event_post_handler};

    esp_http_client_handle_t client = esp_http_client_init(&config_post);
    ESP_ERROR_CHECK(esp_http_client_perform(client));
    ESP_ERROR_CHECK(esp_http_client_cleanup(client));
}

//  Set Scanner parameters
static esp_ble_scan_params_t ble_scan_params = {
    .scan_type = BLE_SCAN_TYPE_PASSIVE,
    .own_addr_type = BLE_ADDR_TYPE_PUBLIC,
    .scan_filter_policy = BLE_SCAN_FILTER_ALLOW_ALL,
    .scan_interval = 0x50,
    .scan_window = 0x30,
    .scan_duplicate = BLE_SCAN_DUPLICATE_ENABLE
};

// GAP callback
static void gap_event_handler(esp_gap_ble_cb_event_t BLE_event, esp_ble_gap_cb_param_t *BLEparam)
{
    const char *compare_str = "TAG";
    switch (BLE_event)
    {
    case ESP_GAP_BLE_SCAN_PARAM_SET_COMPLETE_EVT:

        printf("ESP_GAP_BLE_SCAN_PARAM_SET_COMPLETE_EVT\n");
        if (BLEparam->scan_param_cmpl.status == ESP_BT_STATUS_SUCCESS)
        {
            esp_ble_gap_start_scanning(5);
        }
        break;

    case ESP_GAP_BLE_SCAN_RESULT_EVT:

        if (BLEparam->scan_rst.search_evt == ESP_GAP_SEARCH_INQ_RES_EVT)
        {
            uint8_t *tag = NULL;
            uint8_t tag_len = 0;
            tag = esp_ble_resolve_adv_data(BLEparam->scan_rst.ble_adv, ESP_BLE_AD_TYPE_NAME_CMPL, &tag_len);
            char tag_name_str[tag_len];
            memcpy(tag_name_str, tag, tag_len);
            tag_name_str[tag_len] = '\0';

            if (strncmp(tag_name_str, compare_str, 3) == 0)
            {
                char *pos = strchr(tag_name_str, '_');
                char tag_id_c[3];
                if (pos != NULL)
                {
                    strcpy(tag_id_c, pos + 1);
                    int tag_id = atoi(tag_id_c);
                    RSSI[tag_id-OFFSET] = BLEparam->scan_rst.rssi;
                }
            }
        }
        else if (BLEparam->scan_rst.search_evt == ESP_GAP_SEARCH_INQ_CMPL_EVT)
        {
            for(int i = 0;i<sizeof(RSSI);i++)
            {
                if(RSSI[i] != 0)
                {
                    post_data(FS_ID,(i+OFFSET),RSSI[i]);
                }
            }
            ESP_ERROR_CHECK(esp_wifi_disconnect());
            ESP_ERROR_CHECK(esp_wifi_stop());
            ESP_ERROR_CHECK(esp_bluedroid_enable());
            esp_ble_gap_set_scan_params(&ble_scan_params);
        }
        break;
    default:
        break;
    }
}

void app_main()
{
    // Initizalize NVS
    ESP_ERROR_CHECK(nvs_flash_init());
    printf("NVS init Completed\n");

    // Connect to LAN
    LAN_connection();

    // Allocate memory for Bluetooth
    ESP_ERROR_CHECK(esp_bt_controller_mem_release(ESP_BT_MODE_CLASSIC_BT));
    printf("Memory allocated for Bluetooth\n");

    // Initialize Bluetooth with default configurations
    esp_bt_controller_config_t bluetooth_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    esp_bt_controller_init(&bluetooth_cfg);
    printf("BLuetooth Initialization Completed\n");

    // Configure Bluetoth Low Energy mode
    esp_bt_controller_enable(ESP_BT_MODE_BLE);
    printf("- BT controller enabled in BLE mode\n");

    // Initialize and enable Bluetooth
    esp_bluedroid_init();
    esp_bluedroid_enable();

    // register GAP callback function
    ESP_ERROR_CHECK(esp_ble_gap_register_callback(gap_event_handler));
    printf("- GAP callback registered\n\n");

    // configure scan parameters
    esp_ble_gap_set_scan_params(&ble_scan_params);
}
