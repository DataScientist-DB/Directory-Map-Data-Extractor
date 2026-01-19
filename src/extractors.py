async def extract_listing(element, fields):
    data = {}

    for field, selector in fields.items():
        try:
            loc = element.locator(selector)
            data[field] = (await loc.inner_text()).strip()
        except:
            data[field] = None

    return data
